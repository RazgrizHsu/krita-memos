try:
    from .plugin import index
except Exception as e:
    import traceback
    print("Memos Loading Failed:")
    print(str(e))
    print(traceback.format_exc())
