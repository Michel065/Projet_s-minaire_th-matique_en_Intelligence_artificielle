import tool as tl
import train as tr
import build_data as bd

class IVTSession:
    def __init__(self,source):
        self.source = source
        self.batch_size = 64
        self.output_dir = "./model"
        self.dataset_train = None
        self.dataset_val   = None
        self.dataset_test  = None

        self.image_pour_test = []

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
            self.load_model(name_model,output_dir)
            
        return tl.calculs_seuils(self.model,self.dataset_val,self.source)

    def eval_test_avec_seuils(self):
        return tl.evaluation(self.model,self.dataset_test,self.source)
    
    def load_train_status(self):
        return tr.load_train_status(self.output_dir)
    
    def load_model(self,output_dir="../model",name_model="cnn"):
        self.model=tr.load_model(name_model,output_dir)
        self.output_dir= output_dir
        return self.model

    def load_images_pour_test(self,mode="single",image_path="",folder_path="",nb_random=1):
        if(mode=="single"):
            if(bd.verif_image_existe(image_path)):
                self.image_pour_test = [image_path]
            else:
                raise FileNotFoundError(f"Image introuvable : {image_path}")
        elif(mode == "folder"):
            self.image_pour_test = bd.recup_aleatoirement_x_image_from_dir(folder_path,nb_random)
        return self.image_pour_test

    def predict_ivt(self,use_per_class=True):
        return tl.prediction(self.model,use_per_class,self.image_pour_test,self.source)