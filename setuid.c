#include<errno.h>
#include<stdio.h>
#include<stdlib.h>
#include<unistd.h>

#define err(x) write(2,(x),sizeof(x))

int main(int argc, char **argv)
{
    if(argc < 3) {
        err("Need more args\n");
        exit(1);
    }
    char *end;
    int uid = strtol(argv[1], &end, 10);
    if (*end || !*argv[1]) {
        err("Bad UID format\n");
        exit(1);
    }
    if (setuid(uid)) {
        perror("Can't setuid");
        exit(2);
    }
    execve(argv[2], argv + 2, NULL);
    perror("Exec failed");
    exit(3);
}
