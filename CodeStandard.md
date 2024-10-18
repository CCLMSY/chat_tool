# 结对项目Python规范
本文档是本项目对Python代码一些规范的摘要，用于统一项目代码风格，提高代码可读性和可维护性。

参考文档：[代码规范](https://github.com/shendeguize/GooglePythonStyleGuideCN.git)

## 命名规范
1. **包名/模块名/函数名/方法名/变量名/对象名**：全小写，单词之间用下划线连接，简短有意义
2. **常量名**：全大写，单词之间用下划线连接
3. **类名/异常名**：大驼峰，不使用间隔符，每个单词首字母大写
4. **保护属性/方法名**：以单个下划线开头

### 推荐的命名示例
| **类型** | **公共** | **内部** |
| --- | --- | --- |
| 包 | `lower_with_under` |  |
| 模块 | `lower_with_under` | `_lower_with_under` |
| 类 | `CapWords` | `_CapWords` |
| 异常 | `CapWords` |  |
| 函数 | `lower_with_under()` | `_lower_with_under()` |
| 全局/类常量 | `CAPS_WITH_UNDER` | `_CAPS_WITH_UNDER` |
| 全局/类变量 | `lower_with_under` | `_lower_with_under` |
| 实例变量 | `lower_with_under` | `_lower_with_under`(受保护) |
| 方法名 | `lower_with_under()` | `_lower_with_under()`(受保护) |
| 函数/方法参数 | `lower_with_under` |  |
| 局部变量 | `lower_with_under` |  |

## 风格规范
1. 一行一句代码，不使用分号
2. 除特别明显的功能外，尽量一行只做一个操作
3. 一般语句的最长长度为80个字符
4. 对于长语句，使用括号来隐式连接行，而不是使用反斜杠`\`：
```Python
x = ('This will build a very long long '
     'long long long long long long string')
```
5. 缩进：只使用空格缩进（一般编辑器Tab即可），每级缩进4个空格
6. 空行：在顶级定义(函数或类)之间要间隔两行。在方法定义之间以及class所在行与第一个方法之间要空一行。
7. 函数/方法的参数列表，**每行一个参数**，每个参数后应当有类型提示，必要时对参数进行注释说明：
```Python
def func(a: int,
    b: str, # 参数b的说明
    c: float = 0.0,
    *args,
    **kwargs) -> list[int]:
    pass
```
8. import语句应当按照以下顺序分组：
    1. Python未来版本import语句（例如：`from __future__ import division`）
    2. Python标准基础库import（例如：`import os`）
    3. 第三方库或包的import（例如：`import numpy as np`）
    4. 代码库内子包import（例如：`from mypkg import mymodule`）
9. mian函数应当写在`if __name__ == '__main__':`之下

## 注释规范
### 模块
每个模块都应该要有注释，写在模块的最开头位置，描述模块的内容和使用方法。
示例：
```Python
"""模块或程序的一行摘要，以句号结束。

该文档字符串的其余部分应包含对模块或程序的总体详细描述。
也可选择导出类和函数的简要说明和/或使用示例。
"""
```

### 函数/方法
每个函数/方法都应该要有注释，写在函数/方法声明的下一行。
注释应当包含：函数/方法的功能、输入参数、返回值、异常情况。
示例：
```Python
def sort(arr: list[int], stable: bool = False, reverse: bool = False) -> list[int]:
    """对给定列表进行排序。（函数或方法的一行摘要，以句号结束。）

    对给定列表进行排序，可选择是否稳定排序和是否逆序排序，返回排序后的列表。（函数或方法的详细描述。）

    Args:（函数或方法的输入参数。）
        arr: 待排序的列表。
        stable: 是否稳定排序，默认为False。
        reverse: 是否逆序排序，默认为False。

    Returns:（函数或方法的返回值。）
        排序后的列表。

    Raises:（函数或方法可能引发的异常情况。）
        TypeError: 输入的列表不是整数列表。
    """
    pass
```

### 类
每个类都应该要有注释，写在类声明的下一行，描述类的功能和使用方法。
类内部的方法也应该要有注释，标准格式与函数/方法注释相同。
示例：
```Python
class MyClass:
    """类的一行摘要，以句号结束。

    该文档字符串的其余部分应包含对类的总体详细描述。
    
    Attributes:（类的属性。）
        attr1: 属性1的描述。
        attr2: 属性2的描述。
    """
    pass
```

### 块注释/行注释
在实现某个功能逻辑的代码块之上应当加入注释，代码块间应当空一行。