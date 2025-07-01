#!/bin/bash
cd /root/supermcp || exit 1
git reset --hard HEAD
git pull origin main
docker-compose build
docker-compose up -d
