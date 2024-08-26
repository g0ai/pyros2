
import argparse
import os



def main():
    print("Welcome to pyros2, the pythonic ROS clone!")
    
    parser = argparse.ArgumentParser()
    parser.add_argument("launch", action='store_true')
    parser.add_argument("nodes", action='store_false')



    args = parser.parse_args()

    if args.nodes:
        print("List of running nodes: ")
        # TODO
    
    if args.launch:
        if os.path.basename(os.getcwd()) == "launch":
            default_file = "default.py"
            if os.path.isfile(default_file):
                





if __name__=="__main__":
    main()