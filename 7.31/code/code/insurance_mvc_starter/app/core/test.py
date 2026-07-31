def out(f=10, g=20):
    def inner():
        print(f, g)
    return inner

i = out()
i()