<#
.SYNOPSIS
    Photograph the desktop application.

.DESCRIPTION
    Used by the interface job to capture the application while it is on screen.
    Windows runners provide a graphical session, so the window renders normally.

    Give -ProcessId to capture just that process's window, which keeps the rest
    of the runner desktop out of the picture and makes the image usable as
    documentation. The window handle is read from the process itself rather than
    matched by title, because the title is translated at run time. Falls back to
    the whole screen when no window can be located.
#>
param(
    [Parameter(Mandatory = $true)][string]$Path,
    [int]$ProcessId,
    [int]$TimeoutSeconds = 20
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

Add-Type @'
using System;
using System.Runtime.InteropServices;

public struct RECT { public int Left, Top, Right, Bottom; }

public static class Win32 {
    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);

    [DllImport("dwmapi.dll")]
    public static extern int DwmGetWindowAttribute(
        IntPtr hwnd, int attribute, out RECT value, int size);

    // The window rectangle includes an invisible resize border; the extended
    // frame bounds are what the user actually sees.
    public const int ExtendedFrameBounds = 9;

    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);
}
'@

$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$origin = $screen.Location
$size = $screen.Size

if ($ProcessId) {
    $handle = [IntPtr]::Zero
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
        if (-not $process) { break }
        $process.Refresh()
        if ($process.MainWindowHandle -ne [IntPtr]::Zero -and
            [Win32]::IsWindowVisible($process.MainWindowHandle)) {
            $handle = $process.MainWindowHandle
            break
        }
        Start-Sleep -Milliseconds 400
    }

    if ($handle -ne [IntPtr]::Zero) {
        [void][Win32]::SetForegroundWindow($handle)
        Start-Sleep -Milliseconds 800
        $rect = New-Object RECT
        $ok = [Win32]::DwmGetWindowAttribute(
            $handle, [Win32]::ExtendedFrameBounds, [ref]$rect, 16) -eq 0
        if (-not $ok) { $ok = [Win32]::GetWindowRect($handle, [ref]$rect) }
        if ($ok) {
            $width = $rect.Right - $rect.Left
            $height = $rect.Bottom - $rect.Top
            if ($width -gt 0 -and $height -gt 0) {
                # Clamp to the screen: an off-screen edge cannot be captured.
                $left = [Math]::Max($rect.Left, $screen.Left)
                $top = [Math]::Max($rect.Top, $screen.Top)
                $right = [Math]::Min($rect.Right, $screen.Right)
                $bottom = [Math]::Min($rect.Bottom, $screen.Bottom)
                $origin = New-Object System.Drawing.Point $left, $top
                $size = New-Object System.Drawing.Size ($right - $left), ($bottom - $top)
                Write-Host "Capturing the window of process $ProcessId"
            }
        }
    } else {
        Write-Host "No visible window for process $ProcessId; capturing the whole screen"
    }
}

$bitmap = New-Object System.Drawing.Bitmap $size.Width, $size.Height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($origin, [System.Drawing.Point]::Empty, $size)
$bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bitmap.Dispose()

Write-Host "Saved $Path ($($size.Width)x$($size.Height))"
