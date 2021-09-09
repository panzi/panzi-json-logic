from . import jsonLogic

if __name__ == '__main__':
    import sys
    import json

    logic  = json.loads(sys.argv[1]) if len(sys.argv) > 1 else None
    data   = json.loads(sys.argv[2]) if len(sys.argv) > 2 else None
    result = jsonLogic(logic, data)
    json.dump(result, sys.stdout)
    sys.stdout.write('\n')
