#!/bin/sh
now=$(date -u +%s)
now_offset=$((now - (now % 600) - (60 * 30))) # Half an hour ago rounded down to nearest 10 mins

width=550
zoomlevel=4

url_base=http://himawari8-dl.nict.go.jp/himawari8/img/D531106/${zoomlevel}d/$width/$(date -d @"$now_offset" +%Y/%m/%d/%H%M%S)

tempdir=
cleanup() { rc=$?; rm -rf -- "$tempdir"; trap - EXIT; exit "$rc"; }
trap cleanup EXIT INT HUP TERM
tempdir=$(mktemp -d)
cd -- "$tempdir"

blocks=$(seq 0 "$((zoomlevel-1))")
for y in $blocks; do
    for x in $blocks; do
        url=${url_base}_${x}_${y}.png
        printf %s\\n "$url"
    done
done | {
    set --
    while IFS= read -r url; do
        set -- "$@" "$url"
    done
    printf %s\\n "$@" | wget -qi-
    for arg do set -- "$@" "$(basename -- "$arg")"; done
    shift "$(($#/2))" # Lol hack
    montage "$@" -geometry +0+0 -tile "${zoomlevel}x${zoomlevel}" png:- | feh --bg-max -
}
