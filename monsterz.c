#include <sys/types.h>
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>

/*
 * monsterz.c: setgid wrapper for monsterz.py
 *
 * Copyright: (c) 2005 Sam Hocevar <sam@zoy.org>
 *   This program is free software; you can redistribute it and/or
 *   modify it under the terms of the Do What The Fuck You Want To
 *   Public License, Version 2, as published by Sam Hocevar. See
 *   http://sam.zoy.org/projects/COPYING.WTFPL for more details.
 */

int main(int argc, char **argv)
{
    char buffer[BUFSIZ];
    char *data = DATADIR;
    char *script = DATADIR "/monsterz.py";
    char *score = SCOREFILE;
    char *outfd = "42";
    char **newargv;
    int ret, pos = 0, gid, egid, fd[2];

    egid = getegid();
    gid = getgid();
    if (pipe(fd) < 0) {
      fprintf(stderr, "pipe() failed: %s\n", strerror(errno));
      return 1;
    }

    /* Spawn a child, drop privileges and run our script in the father */
    switch(fork())
    {
        case 0: /* child */
            close(fd[1]);
            break;
        case -1: /* error */
            return 1;
        default: /* father */
            close(fd[0]);
            if (dup2(fd[1], atoi(outfd)) < 0) {
              fprintf(stderr, "dup2 failed: %s\n", strerror(errno));
              return 1;
	    }
            /* drop privileges */
            if(egid != gid)
                setegid(gid);
            /* build a new argument vector */
            newargv = malloc((argc + 7) * sizeof(char *));
            for(pos = 1; pos < argc; pos++)
                newargv[pos] = argv[pos];
            newargv[0] = script;
            newargv[argc++] = "--outfd";
            newargv[argc++] = outfd;
            newargv[argc++] = "--data";
            newargv[argc++] = data;
            newargv[argc++] = "--score";
            newargv[argc++] = score;
            newargv[argc] = NULL;
            /* run our script */
            execv(script, newargv);
            fprintf(stderr, "%s: could not start `%s': %s\n", argv[0], script, strerror(errno));
            return 1;
    }

    /* Handle our child’s messages */
    for(;;)
    {
        ret = read(fd[0], buffer + pos, 1);
        if(ret <= 0)
            break; /* EOF or error */

        if(buffer[pos] == '\n' && buffer[pos - 1] == '\n')
        {
            FILE *f = fopen(score, "w");
            buffer[pos] = '\0'; pos = 0;
            if(f)
            {
                fprintf(f, "%s", buffer);
                fclose(f);
            }
            else
                fprintf(stderr, "%s: unable to write score file `%s'\n",
                        argv[0], score);
        }
        else if(pos++ >= BUFSIZ - 8)
            return 1; /* The script is doing nasty stuff... quit */
    }

    return 0;
}

