
import argparse
import os



def main():
    print("Welcome to pyros2, the pythonic ROS clone!")
    
    parser = argparse.ArgumentParser()
    parser.add_argument("nolaunch", action='store_false') # store_true
    parser.add_argument("nodes", action='store_false')
    parser.add_argument("-r", "--replay", nargs = '*')



    args = parser.parse_args()

    if args.nodes:
        print("List of running nodes: ")
        # TODO
    
    if not args.nolaunch:
        if os.path.basename(os.getcwd()) == "launch":
            default_file = "default.py"
            if os.path.isfile(default_file):
                pass
    
    if args.replay:
        from pyros2.nodes.playback import replay_dbm
        replay_dbm(*args.replay)





if __name__=="__main__":
    main()