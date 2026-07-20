

def number_rabbit(month):
  if month <=2:
    return 1
  else:
    return number_rabbit(month-1) + number_rabbit(month-2)

def main(month):
  res = number_rabbit(month)
  print(res)



if __name__ == "__main__":
  main(9)