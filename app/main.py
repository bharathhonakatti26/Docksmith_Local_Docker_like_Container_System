import os

def main():
    print('App started')
    # show file created by RUN (if present)
    try:
        with open('hello.txt', 'r') as f:
            print('hello.txt contents:')
            print(f.read())
    except FileNotFoundError:
        print('hello.txt not found')
    print('ENV MODE =', os.environ.get('MODE'))


if __name__ == '__main__':
    main()
