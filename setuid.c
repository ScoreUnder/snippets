#include<errno.h>
#include<stdio.h>
#include<stdlib.h>
#include<unistd.h>
#include<err.h>

int main(int argc, char **argv)
{
    if(argc < 3) errx(1, "Need more args");
    char *end;
    int uid = strtol(argv[1], &end, 10);
    if (*end || !*argv[1]) errx(1, "Bad UID format\n");
    if (setuid(uid)) err(2, "Can't setuid");
    execve(argv[2], argv + 2, NULL);
    err(3, "Exec failed");
}
