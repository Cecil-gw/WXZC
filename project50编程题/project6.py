def demo(m,n):
  if m>n:
    temp = m
    m = n
    n = temp
  if m==n or m==1: 
    return m
  elif n%m==0:
    return m
  else:
    return demo(m,n%m)

def demo2(m,n):
  s=demo(m,n)
  return m*n//s

if __name__ == '__main__':
  print(demo(3,6))
  print(demo2(8,6))