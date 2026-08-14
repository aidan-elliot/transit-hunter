Add-Type -AssemblyName System.Drawing

$outputPath = 'C:\Users\aidan\OneDrive\Documents\ChatGPT\Final Project - PHY4000\report-assets\pipeline_diagram.png'
$width = 1600
$height = 920
$bitmap = New-Object System.Drawing.Bitmap($width, $height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$graphics.Clear([System.Drawing.Color]::White)

$dark = [System.Drawing.ColorTranslator]::FromHtml('#7C2D12')
$orange = [System.Drawing.ColorTranslator]::FromHtml('#D97706')
$gold = [System.Drawing.ColorTranslator]::FromHtml('#F59E0B')
$pale = [System.Drawing.ColorTranslator]::FromHtml('#FFF8E7')
$stageFill = [System.Drawing.ColorTranslator]::FromHtml('#FFE4A3')
$diagFill = [System.Drawing.ColorTranslator]::FromHtml('#FFF1B8')
$resultFill = [System.Drawing.ColorTranslator]::FromHtml('#F6D365')
$textColor = [System.Drawing.ColorTranslator]::FromHtml('#3B2518')
$muted = [System.Drawing.ColorTranslator]::FromHtml('#6B4A32')

$titleFont = New-Object System.Drawing.Font('Arial', 27, [System.Drawing.FontStyle]::Bold)
$labelFont = New-Object System.Drawing.Font('Arial', 19, [System.Drawing.FontStyle]::Bold)
$smallFont = New-Object System.Drawing.Font('Arial', 14, [System.Drawing.FontStyle]::Regular)
$titleBrush = New-Object System.Drawing.SolidBrush($dark)
$textBrush = New-Object System.Drawing.SolidBrush($textColor)
$mutedBrush = New-Object System.Drawing.SolidBrush($muted)
$arrowPen = New-Object System.Drawing.Pen($orange, 4)
$arrowPen.CustomEndCap = New-Object System.Drawing.Drawing2D.AdjustableArrowCap(6, 7, $true)

function New-RoundedPath([float]$x, [float]$y, [float]$w, [float]$h, [float]$radius) {
    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $d = $radius * 2
    $path.AddArc($x, $y, $d, $d, 180, 90)
    $path.AddArc($x + $w - $d, $y, $d, $d, 270, 90)
    $path.AddArc($x + $w - $d, $y + $h - $d, $d, $d, 0, 90)
    $path.AddArc($x, $y + $h - $d, $d, $d, 90, 90)
    $path.CloseFigure()
    return $path
}

function Draw-Box([float]$x, [float]$y, [float]$w, [float]$h, [System.Drawing.Color]$fill, [string]$title, [string]$subtitle = '', [bool]$isStage = $false) {
    $path = New-RoundedPath $x $y $w $h 16
    $shadowPath = New-RoundedPath ($x + 5) ($y + 6) $w $h 16
    $shadowBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(32, 124, 45, 18))
    $graphics.FillPath($shadowBrush, $shadowPath)
    $shadowBrush.Dispose()
    $shadowPath.Dispose()
    $fillBrush = New-Object System.Drawing.SolidBrush($fill)
    $borderPen = New-Object System.Drawing.Pen($(if ($isStage) { $dark } else { $orange }), $(if ($isStage) { 4 } else { 3 }))
    $graphics.FillPath($fillBrush, $path)
    $graphics.DrawPath($borderPen, $path)
    $fillBrush.Dispose()
    $borderPen.Dispose()
    $path.Dispose()

    $lines = New-Object 'System.Collections.Generic.List[string]'
    $lines.Add($title)
    if (-not [string]::IsNullOrWhiteSpace($subtitle)) { $lines.Add($subtitle) }
    $total = if ($lines.Count -eq 1) { 30 } else { 60 }
    $cursorY = $y + (($h - $total) / 2)
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $font = if ($i -eq 0 -or (($lines[$i]).Length -le 28 -and -not $isStage)) { $labelFont } else { $smallFont }
        $brush = if ($font -eq $labelFont) { $textBrush } else { $mutedBrush }
        $format = New-Object System.Drawing.StringFormat
        $format.Alignment = [System.Drawing.StringAlignment]::Center
        $format.LineAlignment = [System.Drawing.StringAlignment]::Center
        $rectHeight = if ($font -eq $labelFont) { 30 } else { 24 }
        $rect = [System.Drawing.RectangleF]::new([float]($x + 10), [float]$cursorY, [float]($w - 20), [float]$rectHeight)
        $graphics.DrawString($lines[$i], $font, $brush, $rect, $format)
        $format.Dispose()
        $cursorY += $(if ($font -eq $labelFont) { 31 } else { 25 })
    }
}

function Draw-Arrow([float]$x1, [float]$y1, [float]$x2, [float]$y2) {
    $graphics.DrawLine($arrowPen, $x1, $y1, $x2, $y2)
}

$titleFormat = New-Object System.Drawing.StringFormat
$titleFormat.Alignment = [System.Drawing.StringAlignment]::Center
$graphics.DrawString('Implemented TESS transit-candidate vetting pipeline', $titleFont, $titleBrush, (New-Object System.Drawing.RectangleF(0, 22, $width, 55)), $titleFormat)
$titleFormat.Dispose()

Draw-Box 45 105 285 100 $pale 'Frozen TOI' 'catalogue snapshot'
Draw-Box 425 105 285 100 $pale 'Label and' 'availability audit'
Draw-Box 805 105 285 100 $pale 'SPOC 120-second' 'light curves'
Draw-Box 1190 105 260 100 $pale 'BLS search'
Draw-Arrow 330 155 425 155
Draw-Arrow 710 155 805 155
Draw-Arrow 1090 155 1190 155

Draw-Box 790 330 390 120 $stageFill 'Global and local' 'phase-folded views'
Draw-Box 175 330 480 120 $diagFill 'BLS and vetting diagnostics' 'Odd/even, secondary, symmetry, sectors'
Draw-Box 790 565 390 125 $stageFill 'Stage 1' 'Two-branch 1D CNN' $true
Draw-Box 410 565 300 125 $stageFill 'Stage 2' 'Logistic regression' $true
Draw-Box 420 790 720 92 $resultFill 'Candidate score and validation-selected threshold' 'Ranks candidates; does not confirm planets' $true

$graphics.DrawBezier($arrowPen, 1320, 205, 1320, 260, 1100, 270, 1020, 330)
$graphics.DrawBezier($arrowPen, 1240, 205, 1100, 270, 640, 265, 540, 330)
Draw-Arrow 985 450 985 565
$graphics.DrawBezier($arrowPen, 415, 450, 415, 505, 515, 515, 550, 565)
Draw-Arrow 790 627 710 627
$graphics.DrawBezier($arrowPen, 560, 690, 560, 745, 690, 755, 735, 790)

$footerFormat = New-Object System.Drawing.StringFormat
$footerFormat.Alignment = [System.Drawing.StringAlignment]::Far
$graphics.DrawString('Transit Hunter', $smallFont, $mutedBrush, (New-Object System.Drawing.RectangleF(0, 890, 1545, 24)), $footerFormat)
$footerFormat.Dispose()

$bitmap.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)

$arrowPen.Dispose()
$titleBrush.Dispose()
$textBrush.Dispose()
$mutedBrush.Dispose()
$titleFont.Dispose()
$labelFont.Dispose()
$smallFont.Dispose()
$graphics.Dispose()
$bitmap.Dispose()

Write-Output $outputPath
