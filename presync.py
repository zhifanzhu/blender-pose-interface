from libzhifan import io

f_start = 88985
f_end = 89085

lines = []
for f in range(f_start, f_end):
    # line = f'/media/skynet/DATA/Zhifan/epic/rgb_root/P22/P22_07/frame_{f:010d}.jpg'
    line = f'./P22/P22_07/frame_{f:010d}.jpg'
    lines.append(line)

io.write_txt(lines, 'rsync.txt')