#!/usr/bin/perl -p
s/\^(.)/chr(ord($1) - 64)/eg;
s/M-(.)/chr(ord($1) + 128)/eg;
