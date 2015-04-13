這個repo是來自
https://github.com/vinodc/gitlab-webhook-branch-deployer
的精簡版本

請安裝python2.6

這個repo使用argparse去判別參數，請先安裝argparse

程式用utf-8支持中文
```
easy_install argparse
```
# 如何使用
```
$ ./gitlab-webhook.py --port 8000 git@github.com:vinodc/gitlab-webhook-branch-deployer.git /home/vinod/gwbd
```
監聽8000埠，並且接收由gitlab webhook回傳的 POST json。當回傳的repository為```vinodc/gitlab-webhook-branch-deployer.git```時才會觸發動作。

當觸發時則會更新參數中所帶的位置```/home/vinod/gwbd```

為了確保不會被相似名稱的branch覆蓋，任何branch中有含"/"字元的要求將會被忽略

# 額外選項
```-d True```
這會讓 git 的資訊被刪除，適合發布到線上環境

# 引用
https://github.com/shawn-sterling/gitlab-webhook-receiver

https://github.com/vinodc/gitlab-webhook-branch-deployer

# License

GPLv2
