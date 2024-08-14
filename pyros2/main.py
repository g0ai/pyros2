
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("nodes", action='store_true')



    args = parser.parse_args()

    if args.nodes:
        print("List of running nodes: ")
        # TODO



if __name__=="__main__":
    main()