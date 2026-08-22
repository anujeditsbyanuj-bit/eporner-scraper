mkdir -p videos
> dloads.txt

COOKIE='PHPSESSID=f8ce7430331ba55392325ba9db32506c; EPRNS=9beaf0cfc7edb2b264ccad258a7c2dfc; ageverif_accepted=T'

while read line; do
    url=$(echo "$line" | sed 's/^[0-9]\+\.//')

    curl -sL \
      -H 'Referer: https://www.eporner.com/' \
      -H 'User-Agent: Mozilla/5.0' \
      -b "$COOKIE" \
      "$url" |
    grep -oP '/dload/[^"]*1080p-av1\.mp4' |
    head -n1 |
    sed 's#^#https://www.eporner.com#' >> dloads.txt

done < urls.txt

aria2c \
  -i dloads.txt \
  -d videos \
  -j10 \
  -x16 \
  -s16 \
  -k1M \
  --continue=true \
  --referer='https://www.eporner.com/' \
  --user-agent='Mozilla/5.0' \
  --header="Cookie: $COOKIE"