# 替换下面的IP和用户名
SERVER_IP="152.32.235.6"
SERVER_USER="root"

# 一键执行
ssh-copy-id $SERVER_USER@$SERVER_IP && \
echo "Host s1
    HostName $SERVER_IP
    User $SERVER_USER
    IdentityFile ~/.ssh/id_rsa" >> ~/.ssh/config && \
echo "✅ 配置完成！现在输入 'ssh s1' 即可连接"