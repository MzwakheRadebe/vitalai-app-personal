Param(
  [switch]$Install
)

Set-Location -Path "$PSScriptRoot\frontend"

if ($Install) {
  npm install
}

npm run react
