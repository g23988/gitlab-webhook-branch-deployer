#!/usr/bin/env python
#-*- coding: UTF-8 -*-

import os
import json
import argparse
import BaseHTTPServer
import shlex
import subprocess
import shutil
import logging

logger = logging.getLogger('gitlab-webhook-processor')
logger.setLevel(logging.DEBUG)
logging_handler = logging.StreamHandler()
logging_handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)s %(message)s",
                      "%B %d %H:%M:%S"))
logger.addHandler(logging_handler)

repository = ''
branch_dir = ''


class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_POST(self):
        logger.info("抄收POST資料")
        self.rfile._sock.settimeout(5)

        if not self.headers.has_key('Content-Length'):
            return self.error_response()

        json_data = self.rfile.read(
            int(self.headers['Content-Length'])).decode('utf-8')
        try:
            data = json.loads(json_data)
        except ValueError:
            logger.error("Unable to load JSON data '%s'" % json_data)
            return self.error_response()
	data_repository = data.get('repository', {}).get('url')
	data_user_name = data.get('user_name')
	git_http_url = data.get('repository', {}).get('git_http_url')
	git_ssh_url = data.get('repository', {}).get('git_ssh_url')
	logger.info("觸發者：%s" % data_user_name.encode('utf-8'))
	logger.info("gitHttp：%s" % git_http_url.encode('utf-8'))
	logger.info("gitSSH：%s" % git_ssh_url.encode('utf-8'))
	if data_repository == repository:
		logger.info("確認成功，開始進行更新任務")
		branch_to_update = data.get('ref', '').split('refs/heads/')[-1]
		branch_to_update = branch_to_update.replace('; ', '')
		logger.info("擷取branch名稱%s" % branch_to_update.encode('utf-8'))
		if branch_to_update == '':
                	logger.error("Unable to identify branch to update: '%s'" % data.get('ref', ''))
			return self.error_response()
          	elif (branch_to_update.find("/") != -1 or branch_to_update in ['.', '..']):
                	logger.debug("Skipping update for branch '%s'." % branch_to_update)
		else:
			self.ok_response()
			branch_deletion = data['after'].replace('0', '') == ''
                	branch_addition = data['before'].replace('0', '') == ''
			if branch_addition:
				self.add_branch(branch_to_update)
			elif branch_deletion:
				self.remove_branch(branch_to_update)
			else:
				self.update_branch(branch_to_update)
			return
	else:
		logger.debug(("Repository名稱不符合 '%s' 不等於  '%s "
                          "故忽略") % (data_repository.encode('utf-8'), repository.encode('utf-8')))
	self.ok_response()

    def add_branch(self, branch):
	branch_path = os.chdir(os.path.dirname(branch_dir))
        if os.path.isdir(branch_dir):
            return self.update_branch(branch)
        run_command("git clone %s" % repository)
        os.chmod(branch_dir, 0770)
	if deploynogit == True:
	    run_command("rm -rf {0}/.git".format(branch_dir))
            logger.info("新增了 '%s' 並且不帶.git" % branch_dir)
        else:
	    logger.info("新增了 '%s'" % branch_dir)
    def update_branch(self, branch):
        if not os.path.isdir(branch_dir):
            return self.add_branch(branch)
	if deploynogit == True:
	    return self.update_branch_nogit(branch)
	os.chdir(branch_dir)
        run_command("git checkout -f %s" % branch)
        run_command("git clean -fdx")
        run_command("git fetch origin %s" % branch)
        run_command("git reset --hard FETCH_HEAD")
        logger.info("更新 branch '%s'" % branch.encode('utf-8'))
    def update_branch_nogit(self, branch):
        branch_path = os.chdir(branch_dir)
	run_command("git init")
	run_command("git remote add origin %s" % repository)
        run_command("git clean -fdx")
        run_command("git fetch origin %s" % branch)
        run_command("git reset --hard FETCH_HEAD")
        run_command("rm -rf %s/.git" % branch_dir)
	os.chmod(branch_dir, 0770)
        logger.info("更新了 '%s',並且不帶.git" % branch_dir)



	
    def ok_response(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
    def error_response(self):
        self.log_error("Bad Request.")
        self.send_response(400)
        self.send_header("Content-type", "text/plain")
        self.end_headers()



def run_command(command):
    logger.debug("Running command: %s" % command)
    process = subprocess.Popen(shlex.split(command.encode("ascii")),
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    process.wait()
    if process.returncode != 0:
        logger.error("Command '%s' exited with return code %s: %s" %
                     (command, process.returncode, process.stdout.read()))
        return ''
    return process.stdout.read()

def get_arguments():
    parser = argparse.ArgumentParser(description=(
            'Deploy Gitlab branches in repository to a directory.'))
    parser.add_argument('repository', help=(
            'repository location. Example: git@gitlab.company.com:repo'))
    parser.add_argument('branch_dir', help=(
            'directory to clone branches to. Example: /opt/repo'))
    parser.add_argument('-p', '--port', default=9090, metavar='9090',
                        help='server address (host:port). host is optional.')
    parser.add_argument('-d','--deploynogit',default=False,metavar='',help=('部屬時不複製.git，採用git clone'))
    return parser.parse_args()


def main():
    global repository
    global branch_dir
    global deploynogit 
    args = get_arguments()
    repository = args.repository
    branch_dir = os.path.abspath(os.path.expanduser(args.branch_dir))
    address = str(args.port)
    if args.deploynogit != False:
    	deploynogit = True
    else:
	deploynogit = False

    if address.find(':') == -1:
        host = '0.0.0.0'
        port = int(address)
    else:
        host, port = address.split(":", 1)
        port = int(port)
    server = BaseHTTPServer.HTTPServer((host, port), RequestHandler)
    logger.info("pandan自動更新程式，開始監聽於 %s:%s" % (host, port))
    if deploynogit == True:
        logger.info("clone不帶git啟動")
    else:
        logger.info("連同git紀錄一併clone")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    logger.info("Stopping HTTP Server.")
    server.server_close()

if __name__ == '__main__':
    main()
