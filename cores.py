#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
import os
import settings
import git
import HTML
import sqlite3
from time import time
import shlex, subprocess
from optparse import OptionParser

#optparse stuff
def config():
    """Definition for acceptable options with python's optparse library.
    """
    parser = OptionParser(usage='%prog [options] URL', description='Parse '
            'gitrepository at URL and generate commit-statistics to reward'
            'your users')
    parser.add_option('-b', '--branch', dest='branch', default='master',
        help="Branch you'd like to parse when checking out URL.")
    parser.add_option('-t', '--temp', dest='temp', default='tmp/',
        help="Temporary directory you'd like to make a mess in.")

    return parser.parse_args()

def main():
    # adding global vars to the sqlite connect
    # and the cursor, I imaging this isn't the greatest
    # implementation but it seems easy for me. Fee
    # free to re-write it better -- Eric J. Duran :)
    global conn
    global c
    (opts, args) = config()

    #sqlite db
    conn = sqlite3.connect('cores.db')
    conn.text_factory = str
    c = conn.cursor()

    # Set up the sqlite3 db
    setDatabase();

    #the repo we've been asked to parse
    #@TODO: install bleeding-edge gitpython (instead of old debian version),
    # maybe .clone will work, see:
    # - https://github.com/davvid/GitPython/blob/00c5497f190172765cc7a53ff9d8852a26b91676/CHANGES#L63-67

    #git.Git(opts.temp).clone(args[0])


    # close the cursor
    readLogs();
    writeHTML();
    c.close();

def setDatabase():
    # Set up the sqlite3 db
    c.execute('''create table if not exists users
    (username text, count real)''')
    c.execute('''create table if not exists hash
    (hash text, timestampt real)''')
    conn.commit()

def lastHash(hash):
    #Add the last has to the sqlite database
    c.execute('insert into hash values (?, ?)',[ hash, time()])
    conn.commit()

def readLogs():
    os.chdir('drupal')
    logs = subprocess.Popen(settings.GIT_LOG, stdout=subprocess.PIPE, shell=True).stdout.read()
    parseUsers(logs)

def parseUsers(logs):
    lines = logs.splitlines()
    for item in lines:
        item = item.strip().split(":")
        sha = item[0]
        users = item[1]
        if users.startswith(" Issue"):
            commit_message = users.strip()
            commit_message = re.sub('Issue #[0-9]* by ', '', commit_message)
            commit_users = commit_message.split(",")
            for user in commit_users:
                insertUser(user.strip(), sha)
                #lastHash(sha)

def insertUser(username, hash):
    count = getUserCount(username)
    count = count + 1
    if count == 1:
        c.execute('insert into users values (?, ?)',[username, count])
    else:
        c.execute('update users set count = ? where username = ?', [count, username])

    conn.commit()

def getUserCount(username):
    c.execute("select count from users where username = ?", [username])
    values = c.fetchone()
    if not values:
        return 0

    return values[0]

def writeHTML():
    c.execute("select * from users order by count desc")
    results = c.fetchall()
    htmlcode = HTML.table(results)
    f = open('table.html', 'w')
    f.writelines(htmlcode)
    f.close()

if __name__ == '__main__':
    main()

# vim: et:ts=4:sw=4:sts=4

