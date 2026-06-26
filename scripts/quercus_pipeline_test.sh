# for dev purposes if you want run it locally (optional) with your file names in the correct dir
curl.exe -X POST "http://127.0.0.1:8000/quercus/download" `
  -F "files=@quercus_2025_20260616.csv" `
  -F "files=@quercus_2026_20260616.csv" `
  --output quercus_20260616.csv