Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$inputPath = 'C:\Users\aidan\OneDrive\Documents\ChatGPT\Final Project - PHY4000\ElliotA_Final_Project_PHY4000_Final.docx'
$outputPath = 'C:\Github\transit-hunter\.tmp\figure3_word_render.png'
$word = $null
$document = $null

try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open($inputPath, $false, $true)
    if ($document.InlineShapes.Count -lt 3) {
        throw 'The document contains fewer than three inline figures.'
    }
    $figure = $document.InlineShapes.Item(3)
    $figure.Range.Select()
    $word.Selection.CopyAsPicture()
    Start-Sleep -Milliseconds 1500
    $image = [System.Windows.Forms.Clipboard]::GetImage()
    if ($null -eq $image) {
        throw 'Word did not place a rendered image on the clipboard.'
    }
    $image.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $image.Dispose()
    Write-Output $outputPath
}
finally {
    if ($document) { $document.Close($false) }
    if ($word) { $word.Quit() }
}
