<#
.SYNOPSIS
    Save a picture of the primary screen.

.DESCRIPTION
    Used by the interface job to photograph the desktop application while it is
    on screen. Windows runners provide a graphical session, so the window is
    rendered normally and the resulting image is uploaded as a build artifact.
#>
param(
    [Parameter(Mandatory = $true)][string]$Path
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bitmap.Dispose()

Write-Host "Saved $Path ($($bounds.Width)x$($bounds.Height))"
