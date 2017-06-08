#! /usr/bin/env python3.5
#! -*- coding: utf-8 -*-
'''
Created on 27 lip 2015

@author: kamil@justnet.pl
'''

# #############################################################################
# standard modules (moduly z biblioteki standarowej pythona)
# #############################################################################
import os
import sys
import re
import time
import argparse
import subprocess
import pipes
import getpass
import csv
import datetime
import base64
import gzip
import bz2
import xml.etree.ElementTree as ET
import apt
#import uuid
#import types
#import shutil
NAME = __file__
SPLIT_DIR = os.path.dirname(os.path.realpath(NAME))
SCRIPT_DIR = SPLIT_DIR + '/.' + os.path.basename(NAME)
LIB_DIR = SCRIPT_DIR + '/cache/lib/'
TOOLS_PATH = SPLIT_DIR+'/tools/'
TMP_DIR = SPLIT_DIR + '/tmp/'
sys.path.insert(0,LIB_DIR)
#List of lib to install
import_list = [
#   ('sqlalchemy','1.0.8','SQLAlchemy-1.0.8.egg-info'),
#   ('paramiko','1.15.2','paramiko-1.15.2.dist-info'),
#   ('lxml', '3.8.0', 'lxml-3.8.0.dist-info'),
   ('colorama','0.3.3','colorama-0.3.3.egg-info')]

for line in import_list:
   try:
      if os.path.isdir(LIB_DIR+line[2]):
         pass
#         print('Found installed '+line[0]+line[1]+' in '+line[2])
      else:
         try:
            import pip
         except:
            print("Use sudo apt-get install python3-pip")
            sys.exit(1)
         print('No lib '+line[0]+'-'+line[1])
         os.system("python"+sys.version[0:3]+" -m pip install '"+line[0]+'=='+line[1]+"' --target="+LIB_DIR+" -b "+TMP_DIR)
      module_obj = __import__(line[0])
      globals()[line[0]] = module_obj
   except ImportError as e:
      print(line[0]+' is not installed')

# #############################################################################
# constants, global variables
# #############################################################################
OUTPUT_ENCODING = 'utf-8'
LOGGER_PATH = SCRIPT_DIR+'/logfile.xml'
LOG_VERSION = 1.0
TEMP_PATH = SCRIPT_DIR + '/cache/'
PROCEDURE_SERVER = 'jsoft@serv-repo.justnet.pl'
PROCEDURE_PATH = 'storage/install_procedure/'
DIRECTORY = './'
# #############################################################################
# functions
# #############################################################################

#CZYTANIE Z PLIKU
def readfile(file_name):
   try:
      with open(file_name, 'r') as file:
         templines = [line.rstrip('\n') for line in file]
         lines=([])
         for line in templines:
            if not line.startswith('#'):
               lines.append(line)
   except (IOError, OSError):
      print >> sys.stderr, "Can't open file."
      sys.exit(1)
   return lines

# Kolorowanie ok
def print_ok(output):
   print(colorama.Fore.GREEN+output,colorama.Fore.RESET)

# Kolorowanie błędu
def print_err(error):
   print(colorama.Fore.RED+error,colorama.Fore.RESET)

def indent(elem, level=0):
  i = "\n" + level*"  "
  if len(elem):
    if not elem.text or not elem.text.strip():
      elem.text = i + "  "
    if not elem.tail or not elem.tail.strip():
      elem.tail = i
    for elem in elem:
      indent(elem, level+1)
    if not elem.tail or not elem.tail.strip():
      elem.tail = i
  else:
    if level and (not elem.tail or not elem.tail.strip()):
      elem.tail = i

# LOGI
def my_logger(ERROR_FLAG,subcmd,outmsg):
   id_log = 1
   if not os.path.exists(LOGGER_PATH):
      root = ET.Element('root')
      root.set('version','1.0')
   else:
      tree = ET.parse(LOGGER_PATH)
      root = tree.getroot()
      for child in root:
         id_log+=1
   log = ET.SubElement(root, 'log')
   log.set('id_log',str(id_log))
   date = ET.SubElement(log,'date')
   date.text = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')
   cmdline = str()
   for line in sys.argv:
      cmdline += line+' '
   command = ET.SubElement(log,'command')
   command.set('encoding','plain')
   command.text = cmdline
   subcommands = ET.SubElement(log,'subcommands')
   subcommands.set('error_flag',ERROR_FLAG)
   if 'restore' in sys.argv:  
      sub_id=1
      for one in subcmd:
         log = ET.SubElement(subcommands,'log')
         log.set('id_log',str(sub_id))
         command = ET.SubElement(log,'command')
         command.set('encoding','plain')
         command.text = one 
         date = ET.SubElement(log,'date')
         date.text = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')
         output = ET.SubElement(log,'output')
         output.set('encoding','base64')
         output.text = (base64.b64encode(outmsg[sub_id-1].encode(OUTPUT_ENCODING))).decode(OUTPUT_ENCODING)
         sub_id+=1
      indent(root)
   else:
      subcmd_str=str()
      for one in subcmd:
         subcmd_str+=one+','
      subcommands.text = subcmd_str[:-1]
      output = ET.SubElement(log,'output')
      output.set('encoding','base64')
      output.text = outmsg
      indent(root)
   if not os.path.exists(LOGGER_PATH):
      tree = ET.ElementTree(root)
   tree.write(LOGGER_PATH,encoding=OUTPUT_ENCODING,xml_declaration=True,method='xml')
   
def check_version(file_name):
   tree = ET.parse(file_name)
   root = tree.getroot()
   log_ver = root.get('version')
   if str(LOG_VERSION)==str(log_ver):
      return True
   else:
      return False

def check_file(file_name):
   if file_name.endswith('.gz'):
      with gzip.open(file_name, 'rt') as f:
         lines = f.readlines()
         file_name = file_name[:-3]
         open(file_name,'w').writelines(lines)
         return read_unpacked(file_name)
   elif file_name.endswith('.bz2'):
      with bz2.open(file_name, 'rt') as f:
         lines = f.readlines()
         file_name = file_name[:-4]
         open(file_name,'w').writelines(lines)
         return read_unpacked(file_name)
   else:
      return read_unpacked(file_name)

def read_unpacked(file_name):
   if file_name.endswith('.xml') and check_version(file_name):
      lines = readfile(file_name)
      return lines
   elif file_name.endswith('.txt'):
      lines = readfile(file_name)
      return lines
   else:
      try:
         lines = readfile(file_name)
         return lines
      except UnicodeDecodeError:
         print('File with wrong extension. Available .txt,.xml,.bz2,.gz')

# Ściąganie pliku z podanej lokalizacji
def get_resource(path):
   protocole = find_protocole(path)
   fnname = 'get_resource_by_'+protocole 
   try:
      return globals()[fnname](path)
   except Exception as e:
      print('Exception:',e)

def is_from_server(path):
   path = PROCEDURE_PATH+path
   resp = subprocess.call(['ssh',PROCEDURE_SERVER, 'test -e '+pipes.quote(PROCEDURE_PATH)])
   if resp==0:
      return True
   else:
      return False

def find_protocole(path):
   if os.path.isfile(path):
      return 'local'
   elif path.startswith('ssh://'):
      return 'ssh'
   elif path.startswith('http://'):
      return 'http'
   elif path.startswith('https://'):
      return 'https'
   elif path.startswith('ftp://'):
      return 'ftp'
   elif '@' in path and is_from_server(path):
      return 'server'
   else:
      print("Not supported source")

def get_resource_by_ssh(path):
   path = path[6:]
   os.system('scp '+path+ ' ' + TEMP_PATH)
   return TEMP_PATH+os.path.basename(path)
def get_resource_by_ftp(path):
   os.system('wget '+path+ ' -P '+TEMP_PATH) 
   return TEMP_PATH+os.path.basename(path)
def get_resource_by_http(path):
   os.system('wget '+path+ ' -P '+TEMP_PATH)
   return TEMP_PATH+os.path.basename(path)
def get_resource_by_https(path):
   os.system('wget '+path+ ' -P '+TEMP_PATH)
   return TEMP_PATH+os.path.basename(path)
def get_resource_by_local(path):
   return os.path.abspath(path)
def get_resource_by_server(path):
   os.system('scp '+PROCEDURE_SERVER+':~/'+PROCEDURE_PATH+path+'.txt '+TEMP_PATH)
   return TEMP_PATH+os.path.basename(TEMP_PATH+path+'.txt')

# Wywołanie polecenia w terminalu
def os_call(*args,progress_char='*',verbose=1):
   n = 0
   done_cmd = list()  
   out = list()
   for cmd in args:
      time.sleep(2)
      p = subprocess.Popen(cmd,stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, cwd=DIRECTORY)
      (output,err) = p.communicate()
      n = n+1
      ast = progress_char*n
      if err or 'ERROR' in str(output) or 'Exception' in str(output):
         done_cmd.append(cmd)
         ERROR_FLAG = 'T'
         print_err(cmd)
         if err:
            print_err(err.decode(OUTPUT_ENCODING))
            out.append(err.decode(OUTPUT_ENCODING))
            break
         else:
            print_err(output.decode(OUTPUT_ENCODING))
            out.append(output.decode(OUTPUT_ENCODING))
            break
      else:
         ERROR_FLAG = 'F'
         done_cmd.append(cmd)
         out.append(output.decode(OUTPUT_ENCODING))
         if verbose == 2:
            print(ast,end="\r")
            time.sleep(1)
            print_ok(cmd)
            print_ok(output.decode(OUTPUT_ENCODING))
         elif verbose == 1:
            print_ok(output.decode(OUTPUT_ENCODING))
         else:
            print(ast,end='\r')
   return ERROR_FLAG,done_cmd,out

# Paramiko example
def logonssh(server,loginssh,cmd):
   try:
      ssh = paramiko.SSHClient()
      ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
      ssh.connect(server,port=22,username=loginssh,password=getpass.getpass('SSH Password: '))
      stdin,stdout,stderr = ssh.exec_command(cmd)
      output = stdout.readlines()
      error = stderr.readlines()
      if error:
         for line in error:
            print(line)
      else:
         for line in output:
            print(line)
      ssh.close()
   except Exception as e:
      print(e)

# CSV write example
def csv_write(file_name, temp):
   with open(file_name, 'w', newline='') as csvfile:
      writer = csv.writer(csvfile, delimiter=temp)
      writer.writerow(['example','date','for','csv'])
      writer.writerow(['example']*4)
# CSV read example
def csv_read(file_name, temp):
   with open(file_name, 'r', newline='') as csvfile:
      reader = csv.reader(csvfile, delimiter=temp)
      for row in reader:
         print(row)

# SQLAlchemy simple example
def simple_query(query):
   dbpass=getpass.getpass("DB Password: ")
   engine = sqlalchemy.create_engine("mysql+pymysql://sandbox:"+dbpass+"@195.54.47.34/sandbox")
#   engine = sqlalchemy.create_engine(dialect+driver://username:password@host:port/database)
   connection = engine.connect()
   result = connection.execute(query)
   for row in result:
      print(row)
   connection.close()

def check_module_installed(package):
   package = package[11:].split()
   cache = apt.Cache()
   installed = list()
   not_installed = list()
   for one in package:
      try:
         if cache[one].is_installed:
            print_ok(one+' is installed')
         else:
            print_err(one+' is not installed')
            not_installed.append(one)
      except Exception:
         print_err(one+' is not installed')
#         print_err("Use su -c 'apt-get install "+one+"'")
         not_installed.append(one)
   return not_installed

def install_module(not_installed,):
   commands = list()
   password = getpass.getpass('Root password:')
   for one in not_installed:
      commands.append("echo "+password+" | sudo -S apt-get install "+one)
   for one in commands:
      print(one)
      try:
         os.system(one)
         print_ok('Installing complete')
      except Exception as e:
         print_err('Not installed')
         print_err(e)

def check_and_install(package):
   not_installed = check_module_installed(package)
   if not_installed:
      install = input('Install automatically missing package now? Press Y for yes.')
      if install == 'Y' or install == 'y':
         print('installing')
         install_module(not_installed)
      else:
         print_err("Some module are not installed. Use su -c 'apt-get install <module_name>' to install it")
   else:
      print_ok('All required modules are installed')

def dialog_provider(lines):
   password = getpass.getpass('Root password:')
   new_lines = list()
   for line in lines:
      if line.startswith('DIALOG'):
         line = line[9:]
         if 'su' in line or 'sudo' in line:
            temp_line = line.split()
            for index,one in enumerate(temp_line):
               if one == 'su' or one == 'sudo':
                  temp_line.insert(index,'echo '+password+' |')
                  break
            line = (' ').join(temp_line)
         elif 'mysql' in line:
            line+=password
         else: 
            data = input('Enter data.')
            line = 'echo '+data+' | '+line
         new_lines.append(line)
      else:
         new_lines.append(line)
#   for one in new_lines:
#      print(one)
   return new_lines

# #############################################################################
# classes
# #############################################################################

class SomeClass:

   def __init__(self, some_param1, some_param2, some_param3):
      pass

   def some_method(self, some_param1):
      pass

# #############################################################################
# operations
# #############################################################################
def opt_list(opt):
   cmd = 'ls --color tools/'
   ERROR_FLAG,done_cmd,output = os_call(cmd,progress_char='*',verbose=1)
   msg = (base64.b64encode(output[0].encode(OUTPUT_ENCODING))).decode(OUTPUT_ENCODING)
   return ERROR_FLAG,done_cmd,msg

def opt_call(opt):
   cmd = './tools/'+args.call
   ERROR_FLAG,done_cmd,output = os_call(cmd,progress_char='*',verbose=1)
   msg = (base64.b64encode(output[0].encode(OUTPUT_ENCODING))).decode(OUTPUT_ENCODING)
   return ERROR_FLAG,done_cmd,msg

def opt_exec_module(element, *more):
   cmd = './tools/'+element+'/'+element+'.py '
   for one in more:
      cmd += one + ' '
   ERROR_FLAG,done_cmd,out = os_call(cmd,progress_char='*',verbose=1)
   msg = (base64.b64encode(out[0].encode(OUTPUT_ENCODING))).decode(OUTPUT_ENCODING)
   return ERROR_FLAG,done_cmd,msg

def opt_install(opt):
   file_name = get_resource(opt)
   lines = check_file(file_name)
   if lines[0].startswith('REQUIRED'):
      check_and_install(lines[0])
      lines = lines[1:]
   lines = dialog_provider(lines)
#   print(lines)
   ERROR_FLAG,done_cmd,output = os_call(*lines,progress_char='*',verbose=1)
   msg = (base64.b64encode(str(output).encode(OUTPUT_ENCODING))).decode(OUTPUT_ENCODING)
   return ERROR_FLAG,done_cmd,msg

def opt_dest(name,dest):
   file_name = get_resource(name)
   lines = check_file(file_name)
   globals()["DIRECTORY"] = os.path.abspath(dest) 
   ERROR_FLAG,done_cmd,output = os_call(*lines,progress_char='*',verbose=2)
   msg = (base64.b64encode(str(output).encode(OUTPUT_ENCODING))).decode(OUTPUT_ENCODING)
   return ERROR_FLAG,done_cmd,msg

def opt_help():
   parser.print_help()
   msg = 'Printed help'
   msg = (base64.b64encode(('Printed help').encode(OUTPUT_ENCODING))).decode(OUTPUT_ENCODING)
   return msg

def log_brief(LOGGER_PATH,inti):
   tree = ET.parse(LOGGER_PATH)
   root = tree.getroot()
   for log in root.findall('log'):
      idic = log.get('id_log')
      date = log.find('date').text
      cmd = log.find('command').text
      err_flag = log.find('subcommands').get('error_flag')
      line = idic+'\t'+err_flag+'  '+date+'  '+ cmd
      if int(idic) >= inti:
         if err_flag == 'T':
            print_err(line)
         else:
            print_ok(line)

def opt_log(opt,int):
   if opt == 'xml':
      lines = readfile(LOGGER_PATH)
      for line in lines:
         print(line)
   elif opt == 'brief':
      log_brief(LOGGER_PATH,int)
   elif opt == 'header':
      print('id   flag\tdate\t\t\tcommand')
      log_brief(LOGGER_PATH,int) 
   elif opt == 'out':
      print("Printing output line decoded to utf-8")
      tree = ET.parse(LOGGER_PATH)
      root = tree.getroot()
      for log in root.findall('log'):
         if log.findall('output'):
            readed = log.find('output').text
            decoded = base64.b64decode(readed).decode(OUTPUT_ENCODING)
            print(log.get('id_log')+'.','\n'+decoded)
         else:
            if log.findall('subcommands'):       
               subcommands = log.findall('subcommands')
               for sub in subcommands:
                  sublog = sub.findall('log')
                  for out in sublog:
                     output = out.findall('output')
                     for one in output:
                        decoded = base64.b64decode(one.text).decode(OUTPUT_ENCODING)
                        print(log.get('id_log')+'. restored','\n'+decoded)

def opt_dumplog(opt):
   path = os.path.dirname(opt)
   name = os.path.basename(opt)
   if opt.endswith('.xml'):
      cmd = 'scp '+LOGGER_PATH+' '+opt
   elif opt.endswith('.gz'):
      cmd = 'gzip -c '+LOGGER_PATH+' > '+opt
   elif opt.endswith('bz2'):
      cmd = 'bzip2 -czk '+LOGGER_PATH+' > '+opt
   os_call(cmd,progress_char='*',verbose=1)

def opt_restore(opt,*inti):
   file_name = get_resource(opt)
   lines = check_file(file_name)
   linestring = str()
   for line in lines:
      linestring+=line+' ' 
   if lines == False:
      out = 'Log file version is not supported'
      ERROR_FLAG = 'T'
      done_cmd = str()
      for cmd in sys.argv:
         done_cmd += cmd + ' '
      print(out)
      msg = (base64.b64encode(out.encode(OUTPUT_ENCODING))).decode(OUTPUT_ENCODING)
      return ERROR_FLAG,done_cmd,msg
   else:
      if inti[0]: start = inti[0]
      else: start = 1
      cmd_to_do = list()
#      print(file_name)
      tree = ET.fromstring(linestring)
      for log in tree.findall('log'):
         idic = log.get('id_log')
         subcmd = log.find('subcommands').text
         if len(inti) == 2: end = inti[1]
         else: end = int(idic)
         if subcmd and start<=int(idic) and end>=int(idic):
            subcmd = subcmd.split(',')
            for line in subcmd:
               cmd_to_do.append(line)
      ERROR_FLAG,done_cmd,out = os_call(*cmd_to_do,progress_char='*',verbose=2)
      return ERROR_FLAG,done_cmd,out

# #############################################################################
# main app 
# #############################################################################
if __name__ == '__main__':
# Czytanie arugmentów
   parser = argparse.ArgumentParser(prog='jsh.py', description='Justnet shell. Script to install new project and execute wirtual commands, other scripts, tools installed with it.', epilog='Example of usage: ./jsh.py install sza')
# SUBPARSER
   subparsers = parser.add_subparsers()
# INSTALL
   parser_install = subparsers.add_parser('install', help = 'Install new project. Default config file is downloading from server. With dest: see dest')
   parser_install.add_argument('install', nargs='?', help = 'Path to file with procedure to install. It can be ssh,http,https,ftp,local file or from default server which is '+PROCEDURE_SERVER)
   parser_install.add_argument('dest', nargs='?', default='./', help = 'Directory where project will be installed. Default current directory.')
   parser_call = subparsers.add_parser('call', help = 'Execute tools from installed project')
   parser_call.add_argument('call', help = 'Name of used tools with parameters')
# LIST
   parser_list = subparsers.add_parser('list', help = 'Show tools for installed project')
   parser_list.add_argument('list', action='store_true', help = 'List of tools')
   parser_log = subparsers.add_parser('log', help = 'Show logs. Use jsh.py log -h to see options.')
   parser_log.add_argument('log', nargs='?', choices=['brief','xml','header','out'], default='brief',help = '''Show logs.
       xml - Pure xml file.
       brief - List id_log,flag(error or not),date,command.
       header - List like brief but with column title.
       out - Show only decoding output to utf-8.''')
   parser_log.add_argument('--int', type=int,nargs='?', default=1, help='Number of first log')
   parser_restore = subparsers.add_parser('restore', help = 'Processes the log and play back all commands executed')
   parser_restore.add_argument('restore', help = 'Name of file to restore')
   parser_restore.add_argument('--int',type=int, nargs='*', help ='Start num, if 2 num, first is start, second is end. Without any default restore all, with one num restore from start to last one. With two restore from start to end.')
   parser_dumplog = subparsers.add_parser('dumplog', help = 'Backup log to file with extension .xml,.bz2,.gz.')
   parser_dumplog.add_argument('dumplog',nargs='?', default='./jsh.xml.gz', help = 'Backup log to file with extension .xml,.bz2,.gz.')
###### 
# OBSŁUGA ARGUMENTÓW Z TOOLS
   if os.path.isdir(TOOLS_PATH):
      name_arg = next(os.walk(TOOLS_PATH))[1]
      for element in name_arg:
         if not os.path.islink('tools/'+element+'.py'):
            src = os.path.join(element+'/'+element+'.py')
            dst = os.path.join('tools/'+element+'.py')
#            print(src,'-->',dst)
            os.symlink(src,dst)
#            print(element, 'symlink created')
         module_pars = 'parser_'+element
         module_pars = subparsers.add_parser(element, help="To get more about "+element+" use ./jsh.py "+element+" or ./jsh.py "+element+" 'help_info -h'")
         module_pars.add_argument(element, nargs='*', help="To get more help about "+element+" use ./jsh.py "+element+" 'help_info -h' or ./jsh.py "+element)

# OBSŁUGA ARGUMENTÓW
   args = parser.parse_args()
   try:
# Brak argumentów - wyświetl pomoc
      if not len(sys.argv) > 1:
         out = 'Need more argument'
         msg = (base64.b64encode(out.encode(OUTPUT_ENCODING))).decode(OUTPUT_ENCODING)
         cmd = list()
         for one in sys.argv:
            cmd.append(one)
         my_logger('F',cmd,msg)
         opt_help()
      elif 'install' in args and args.dest=='./':
         ERROR_FLAG,done_cmd,msg = opt_install(args.install)
         my_logger(ERROR_FLAG,done_cmd,msg)
      elif 'dest' in args and 'install' in args:
         ERROR_FLAG,done_cmd,msg = opt_dest(args.install,args.dest)
         my_logger(ERROR_FLAG,done_cmd,msg)
      elif 'call' in args:
         ERROR_FLAG,done_cmd,msg = opt_call(args.call)
         my_logger(ERROR_FLAG,done_cmd,msg)
      elif 'list' in args:
         ERROR_FLAG,done_cmd,msg = opt_list(args.list)
         my_logger(ERROR_FLAG,done_cmd,msg)
      elif 'log' in args and not 'int' in args:
         opt_log(args.log)
      elif 'log' in args and 'int' in args:
         opt_log(args.log,args.int)
      elif 'dumplog' in args:
         opt_dumplog(args.dumplog)
      elif 'restore' in args:
         inti = list()
         if args.int == None:
            inti.append(1) 
         else:
            inti = args.int
         ERROR_LOG,done_cmd,msg = opt_restore(args.restore,*inti)
         my_logger(ERROR_LOG,done_cmd,msg)
      elif args:
         for element in name_arg:
            if element in args:
               element_arg = sys.argv[2:]
               ERROR_FLAG,done_cmd,msg = opt_exec_module(element,*element_arg)
               my_logger(ERROR_FLAG,done_cmd,msg)        
      else:
         cmd = list()
         out = 'Wrong argument'
         msg = (base64.b64encode(out.encode(OUTPUT_ENCODING))).decode(OUTPUT_ENCODING)
         for one_arg in sys.argv:
            cmd.append(one_arg)
         my_logger('T',cmd,msg)
         opt_help()
   except Exception as e:
      cmd = str()
      for one_arg in sys.argv:
         cmd+=one_arg+' '
      list_cmd =list()
      list_cmd.append(cmd)
      err_msg = str(e)
      msg = (base64.b64encode(err_msg.encode(OUTPUT_ENCODING))).decode(OUTPUT_ENCODING)
      my_logger('T',list_cmd,msg)
      print(e)
