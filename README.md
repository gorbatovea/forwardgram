# ForwardGram
### About
This script forwards messages through [TG] chats and channels. Backed by [Telethon].

[TG]: https://telegram.org/
[Telethon]: https://github.com/LonamiWebs/Telethon

### Installation
`pip install -r requirements.txt`

### Configuration
Configuration file should be stored at `conf/api_conf.json`.

See `conf/api_conf-example.json`.
#### Where should I get parameters for config file?
https://my.telegram.org/apps

### Redis installation & setup
#### Install
```
docker pull redis:6.2.6
```
#### Run
```
mkdir redis-data 

docker run --name forward-redis -p 127.0.0.1:6379:6379 -v redis-data:/data -d redis:6.2.6 redis-server --save 60 1 --loglevel warning
```
#### Official page
[Redis docker image]

[Redis docker image]:https://hub.docker.com/_/redis?tab=description
### Launch

```
python3 forwardgram.py \
    --cmd <login|forward> 
    --from <forward_from (mandatory when cmd==forward)> \
    --to <forward_to (mandatory when cmd==forward)> \
    --log-path <logs_dir (optional)> \
    --log-file <logs_file_name (optional)>
```