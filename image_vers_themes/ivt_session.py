import tool as tl
import train as tr

class IVTSession:
    def __init__(self,source):
        self.source = source
        self.batch_size = 64
        self.output_dir = "./model"
        self.dataset_train = None
        self.dataset_val   = None
        self.dataset_test  = None

        self.model  = None

    def generer_datasets(self, batch_size: int = 64, boost: bool = True):
        self.dataset_train, self.dataset_val, self.dataset_test = tl.generer_datasets(self.source,batch_size,boost)

    def _datasets_prets(self) -> bool:
        return (self.dataset_train is not None and self.dataset_val is not None and self.dataset_test is not None)

    def train(self, epochs=50,output_dir="../model",name_model="cnn", batch_size: int = 64, boost: bool = True):
        self.output_dir=output_dir
        if not self._datasets_prets():
            self.generer_datasets(batch_size=batch_size, boost=boost)

        self.model,history = tl.entrainement(self.dataset_train, self.dataset_val,source = self.source, EPOCHS=epochs,output_dir=output_dir,name_model=name_model)
        return history

    def compute_seuils(self,output_dir="../model",name_model="cnn"):
        if(self.model is None):
            self.model=tr.load_model(name_model,output_dir)
            self.output_dir= output_dir
        return tl.calculs_seuils(self.model,self.dataset_val,self.source)

    def eval_test_avec_seuils(self):
        return tl.evaluation(self.model,self.dataset_test,self.source)
    
    def load_train_status(self):
        return tr.load_train_status(self.output_dir)
