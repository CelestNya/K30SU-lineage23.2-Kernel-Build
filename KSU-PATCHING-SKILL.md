# KSU Manual Hook 补丁操作指南

## 工作流概述

```
本地内核源码 (gitignored)     patches/ 目录 (git tracked)
┌─────────────────────┐       ┌─────────────────────┐
│ 手动编辑源码文件     │ ──→   │ git diff 生成 .patch │
│ android_kernel_xxx/  │       │ 存入 patches/sukisu/ │
└─────────────────────┘       └─────────┬───────────┘
                                        │ CI 中 patch -p1 应用
                                        ▼
                               ┌─────────────────────┐
                               │ 每次构建自动打补丁   │
                               └─────────────────────┘
```

## 核心文件

| # | 内核文件 | 函数 | Hook 调用 |
|---|---------|------|-----------|
| 1 | `fs/exec.c` | `do_execveat_common` | `ksu_handle_execveat` + `ksu_handle_execveat_sucompat` |
| 2 | `fs/open.c` | `do_faccessat` | `ksu_handle_faccessat` |
| 3 | `fs/read_write.c` | `vfs_read` | `ksu_handle_vfs_read` |
| 4 | `fs/stat.c` | `vfs_statx` | `ksu_handle_stat` |
| 5 | `drivers/input/input.c` | `input_handle_event` | `ksu_handle_input_handle_event`（安全模式救砖） |
| 6 | `fs/devpts/inode.c` | `devpts_get_priv` | `ksu_handle_devpts`（修复 `pm` 命令） |

## 操作步骤

### 1. 修改本地内核源码

```bash
# 内核源码目录是 gitignored 的，不会上传到仓库
cd android_kernel_xiaomi_sm8250/

# 编辑目标文件，例如：
vim fs/exec.c
```

每个文件需要改两处：
- **函数前**：添加 `extern` 声明
- **函数内**：添加 hook 调用

**示例：`fs/exec.c`**

```c
// 函数前加 extern 声明
extern int ksu_handle_execveat(int *fd, struct filename **filename_ptr, void *argv, void *envp, int *flags);
extern int ksu_handle_execveat_sucompat(int *fd, struct filename **filename_ptr, void *argv, void *envp, int *flags);

static int do_execveat_common(int fd, struct filename *filename,
                              struct user_arg_ptr argv,
                              struct user_arg_ptr envp,
                              int flags)
{
    // 函数内加 hook 调用
    ksu_handle_execveat(&fd, &filename, &argv, &envp, &flags);
    ksu_handle_execveat_sucompat(&fd, &filename, &argv, &envp, &flags);
    return __do_execve_file(fd, filename, argv, envp, flags, NULL);
}
```

**各文件的 extern 声明与调用签名：**

| 文件 | extern 声明 | 调用 |
|------|------------|------|
| `fs/exec.c` | `extern int ksu_handle_execveat(int *fd, struct filename **filename_ptr, void *argv, void *envp, int *flags);`<br>`extern int ksu_handle_execveat_sucompat(...);` | `ksu_handle_execveat(&fd, &filename, &argv, &envp, &flags);` |
| `fs/open.c` | `extern int ksu_handle_faccessat(int *dfd, const char __user **filename_user, int *mode);` | `ksu_handle_faccessat(&dfd, &filename, &mode);` |
| `fs/read_write.c` | `extern int ksu_handle_vfs_read(struct file **file_ptr, char __user **buf_ptr, size_t *count_ptr, loff_t **pos);` | `ksu_handle_vfs_read(&file, &buf, &count, &pos);` |
| `fs/stat.c` | `extern int ksu_handle_stat(int *dfd, const char __user **filename_user, int *flags);` | `ksu_handle_stat(&dfd, &filename, &flags);` |
| `drivers/input/input.c` | `extern int ksu_handle_input_handle_event(unsigned int *type, unsigned int *code, int *value);` | `ksu_handle_input_handle_event(&type, &code, &value);`（在 `int disposition = ...` 之后） |
| `fs/devpts/inode.c` | `extern int ksu_handle_devpts(struct inode **inode);` | `ksu_handle_devpts((struct inode **)&dentry);`（在 `{` 之后） |

### 2. 用 git diff 生成补丁

```bash
cd android_kernel_xiaomi_sm8250/

# 逐个文件生成 patch，存入 patches/ 目录
git diff -- fs/exec.c > ../patches/sukisu/01-fs-exec.c.patch
git diff -- fs/open.c > ../patches/sukisu/02-fs-open.c.patch
git diff -- fs/read_write.c > ../patches/sukisu/03-fs-read_write.c.patch
git diff -- fs/stat.c > ../patches/sukisu/04-fs-stat.c.patch
git diff -- drivers/input/input.c > ../patches/sukisu/05-drivers-input-input.c.patch
git diff -- fs/devpts/inode.c > ../patches/sukisu/06-fs-devpts-inode.c.patch
```

### 3. 验证补丁可应用

```bash
# 恢复内核源码改动
git checkout -- .

# 验证 patch 能干净打上
for p in ../patches/sukisu/01-fs-exec.c.patch ../patches/sukisu/02-fs-open.c.patch \
         ../patches/sukisu/03-fs-read_write.c.patch ../patches/sukisu/04-fs-stat.c.patch \
         ../patches/sukisu/05-drivers-input-input.c.patch ../patches/sukisu/06-fs-devpts-inode.c.patch; do
    echo "--- Testing $(basename $p) ---"
    patch -p1 --dry-run -F3 < "$p" 2>&1 | tail -2
done
```

### 4. CI 中应用补丁

```yaml
- name: Apply SukiSU manual hook patches
  run: |
    for p in \
      01-fs-exec.c.patch \
      02-fs-open.c.patch \
      03-fs-read_write.c.patch \
      04-fs-stat.c.patch \
      05-drivers-input-input.c.patch \
      06-fs-devpts-inode.c.patch; do
      echo "Applying $p..."
      patch -p1 -d $KERNEL_PATH < patches/sukisu/$p || echo "WARNING: $p failed"
    done
```

## 注意事项

### .gitignore 规则
- `android_kernel_xiaomi_sm8250/` — **gitignored**，不会推送
- `patches/` — **NOT ignored**，补丁文件正常跟踪
- `.github/workflows/` — **NOT ignored**，CI 工作流正常跟踪

### 内核版本差异
不同 4.19 内核的代码可能有微小偏移，补丁生成后务必 `--dry-run` 测试。

### 多个补丁的依赖顺序
- qcacld-3.0 WiFi patch 和 KSU patch 改的是不同文件，不冲突
- 建议先打 WiFi patch，再打 KSU patch

### SukiSU 集成分阶段
1. **阶段一**（当前）：纯 SukiSU + Manual Hook（`setup.sh | bash -s builtin`）
2. **阶段二**（后续）：加 SUSFS（`setup.sh | bash -s susfs-dev` + SUSFS Kconfig 选项 + KernelPatch）
3. **阶段三**（后续）：加 KPM 模块加载支持
