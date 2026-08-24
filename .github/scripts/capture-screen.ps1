<#
.SYNOPSIS
    Photograph the desktop application.

.DESCRIPTION
    Used by the interface job to capture the application while it is on screen.
    Windows runners provide a graphical session, so the window renders normally.

    With -WindowTitle, only that window is captured, which keeps the rest of the
    runner desktop out of the picture and makes the result usable as
    documentation. Without it, the whole screen is captured.
#>
param(
    [Parameter(Mandatory = $true)][string]$Path,
    [string]$WindowTitle
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

Add-Type @'
using System;
using System.Runtime.InteropServices;

public struct RECT { public int Left, Top, Right, Bottom; }

public static class Win32 {
    [DllImport("user32.dll")]
    public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);

    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);

    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
}
'@

$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$origin = $bounds.Location
$size = $bounds.Size

if ($WindowTitle) {
    $handle = [Win32]::FindWindow($null, $WindowTitle)
    if ($handle -ne [IntPtr]::Zero) {
        [void][Win32]::SetForegroundWindow($handle)
        Start-Sleep -Milliseconds 700
        $rect = New-Object RECT
        if ([Win32]::GetWindowRect($handle, [ref]$rect)) {
            $width = $rect.Right - $rect.Left
            $height = $rect.Bottom - $rect.Top
            if ($width -gt 0 -and $height -gt 0) {
                $origin = New-Object System.Drawing.Point $rect.Left, $rect.Top
                $size = New-Object System.Drawing.Size $width, $height
                Write-Host "Capturing window '$WindowTitle'"
            }
        }
    } else {
        Write-Host "Window '$WindowTitle' not found; capturing the whole screen"
    }
}

$bitmap = New-Object System.Drawing.Bitmap $size.Width, $size.Height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($origin, [System.Drawing.Point]::Empty, $size)
$bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bitmap.Dispose()

Write-Host "Saved $Path ($($size.Width)x$($size.Height))"
