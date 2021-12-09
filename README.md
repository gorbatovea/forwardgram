# ForwardGram
### About
This script forwards messages through [TG] chats and channels. Backed by [Telethon].

[TG]: https://telegram.org/
[Telethon]: https://github.com/LonamiWebs/Telethon

### Installation
`pip install -r requirements.txt`

### Configuration
Configuration file should be stored at `conf/api_conf.json`.
Configuration schema should contain: 
```
{
  "api_id": <api_id>,
  "api_hash": "<api_hsas>"
}
```
#### Where should i get parameters for config file?
https://my.telegram.org/apps

### Launch

```python3 forwardgram.py <command: login|forward> <forward from> <forward to>```