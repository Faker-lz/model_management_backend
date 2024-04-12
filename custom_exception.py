class ModelNotExist(Exception):
    def __init__(self) -> None:
        super().__init__('Model not exist')

class ModelOnlineFail(Exception):
    def __init__(self) -> None:
        super().__init__('Model online fail')

class ModelNotReady(Exception):
    def __init__(self) -> None:
        super().__init__('Model does not ready')

class SshNotExist(Exception):
    def __init__(self) -> None:
        super().__init__("Ssh detail data not")