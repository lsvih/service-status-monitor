# Service Status Monitor
A Tiny dashboard application that could monitor servers, services and GPUs' status. Written in Python3.

![Screenshot](/screenshot.png)

![GPU status](/screenshot-2.png)

![Real-time GPU Usage Statistics](/screenshot-3.png)

### Dependency

- Python3
- Flask
- sqlite
- apscheduler
- Boostrap
- Vue.js
- axios

### Usage

```bash
pip3 install -r requirements.txt
gunicorn -w 4 -b 127.0.0.1:5006 app:app
```

>  `python3 app.py` for development mode.

Then visit [127.0.0.1:5006](127.0.0.1:5006).


Default administrator's username and password:
```
username=root
password=root
```


### Note

There need a account 'monitor' whose password is 'monitor' and which authorized to execute `ps -e` in GPU server.

### Acknowledgement

GPU monitor refer to [https://github.com/congjianluo/GPU-monitor](https://github.com/congjianluo/GPU-monitor)