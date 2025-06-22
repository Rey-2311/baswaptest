import torch
# Workaround for the Torch/Streamlit event loop issue:
torch.classes.__path__ = []

import torch.nn as nn
from pytorch_lightning import LightningModule
from torchmetrics.regression import MeanAbsoluteError, MeanSquaredError, R2Score
import joblib

class LSTMTimeseries(nn.Module):
    def __init__(self, input_size: int, output_size: int, hidden_size: int = 128, dropout: float = 0.5):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers=1, batch_first=True)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc(out)
        return out

class LITModel(LightningModule):
    def __init__(self, input_size: int = 1, output_size: int = 1, hidden_size: int = 128, dropout: float = 0.5, lr: float = 0.001):
        super().__init__()
        self.save_hyperparameters()
        
        self.model = LSTMTimeseries(input_size, output_size, hidden_size, dropout)
        self.criterion = nn.MSELoss()
        self.lr = lr

        self.test_mae = MeanAbsoluteError()
        self.test_mse = MeanSquaredError()
        self.test_r2 = R2Score()

    def forward(self, x):
        return self.model(x)

    def step(self, batch, step_type: str):
        x, y = batch
        pred = self.forward(x)
        loss = self.criterion(pred, y)
        self.log(f'{step_type}_loss', loss, on_step=True, on_epoch=True)
        return loss, pred, y
    
    def training_step(self, batch, batch_nb):
        loss, _, _ = self.step(batch, 'train')
        return loss
    
    def validation_step(self, batch, batch_nb):
        loss, _, _ = self.step(batch, 'val')
        return loss
    
    def test_step(self, batch, batch_nb):
        x, y = batch
        pred = self.forward(x)

        # mae = self.mae(pred, y)
        # mse = self.mse(pred, y)
        # r2 = self.r2(pred, y)
        pred = pred.view(-1)
        y = y.view(-1)
        self.test_mae.update(pred, y)
        self.test_mse.update(pred, y)
        self.test_r2.update(pred, y)
    
    def on_test_epoch_end(self):
        self.log("mae", self.test_mae.compute())
        self.log("mse", self.test_mse.compute())
        self.log("r2", self.test_r2.compute())
        self.test_mae.reset()
        self.test_mse.reset()
        self.test_r2.reset()

    def predict_step(self, batch, batch_nb):
        x, _ = batch
        return self.forward(x)[:, -1, :]
    
    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=self.lr)

def make_predictions(df, mode=None):
    # Convert the test data to a NumPy array and reshape it
    reshaped_df = df.to_numpy().reshape(-1, 1)

    # Transform the test data using the fitted scaler
    scaler = joblib.load("scalers/scaler_vinhlong.pkl")
    scaled_df = scaler.transform(reshaped_df)
    input_seq = torch.tensor(scaled_df, dtype=torch.float32).unsqueeze(0)  # Shape: (1, seq_len, features)
    if mode == "Max":
        model = LITModel.load_from_checkpoint("weights/hourly_max.ckpt")
    model.eval()  # Set model to evaluation mode

    # Make a single prediction
    with torch.no_grad():
        prediction = model(input_seq)[:, -1, :]  # Get the last time step prediction

    rescaled_prediction = scaler.inverse_transform(prediction)
    return [rescaled_prediction.item()]

    