
import argparse


def main():
    print("Welcome to pyros2, the pythonic ROS clone!")
    
    parser = argparse.ArgumentParser()
    parser.add_argument("nodes", action='store_true')



    args = parser.parse_args()

    if args.nodes:
        print("List of running nodes: ")
        # TODO



if __name__=="__main__":
    main()