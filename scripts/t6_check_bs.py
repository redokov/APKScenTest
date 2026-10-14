import glob
p = glob.glob('src/**/Ext/ObjectModule.bsl', recursive=True)[0]
data = open(p, 'rb').read()
BS = bytes([92]); Q = bytes([34])
# old: , "\"", "");   ->  , """", "");
old = bytes([44, 32]) + Q + BS + Q + Q + bytes([44, 32]) + Q + Q + bytes([41, 59])
# new: , """", "");
new = bytes([44, 32]) + Q + Q + Q + Q + bytes([44, 32]) + Q + Q + bytes([41, 59])
n = data.count(old)
print('count:', n)
if n == 1:
    data = data.replace(old, new)
    open(p, 'wb').write(data)
    print('replaced OK')
# verify no stray parse-breaking sequences left: Q BS Q outside comments
i = data.find(Q + BS + Q)
while i != -1:
    print('remaining off', i, repr(data[i-20:i+20]))
    i = data.find(Q + BS + Q, i + 1)
