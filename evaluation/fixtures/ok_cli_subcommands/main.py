import argparse

parser = argparse.ArgumentParser(description="demo tool")
sub = parser.add_subparsers(dest="command", required=True)
sub.add_parser("train", help="train the model")
sub.add_parser("watch", help="watch a trained model")
args = parser.parse_args()
print(f"running {args.command}")
