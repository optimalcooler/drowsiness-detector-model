import torch # Import the main PyTorch library
import torch.nn as nn # Import neural network modules (layers, loss functions, etc.)
import torch.optim as optim # Import optimization algorithms (Adam, SGD, etc.)
from torchvision import datasets, transforms, models # Import computer vision datasets, image transformations, and pre-trained models

def main():
    # 1. Define data transformations
    # We compose several transformations together to be applied to each image
    data_transforms = transforms.Compose([
        # ImageFolder loads images as RGB by default, even if they are grayscale. 
        # ResNet expects 3 channels, so this default behavior works perfectly for us.
        transforms.Resize((224, 224)), # Resize the images to 224x224 pixels, which is the input size ResNet expects
        transforms.ToTensor(), # Convert the images from PIL format to PyTorch Tensors and scale pixel values from [0, 255] to [0.0, 1.0]
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]) # Normalize the tensor images with ImageNet's mean and standard deviation for optimal pre-trained model performance
    ])

    # 2. Load the datasets using ImageFolder
    # ImageFolder expects a directory structure where subfolders represent class labels (e.g., train/awake, train/sleepy)
    # Note: Make sure the 'train' and 'val' folders are in the same directory as this script when you run it.
    train_dataset = datasets.ImageFolder(root='train', transform=data_transforms) # Load the training data and apply the transformations
    val_dataset = datasets.ImageFolder(root='val', transform=data_transforms) # Load the validation data and apply the transformations

    # 3. Create DataLoaders
    # DataLoaders handle batching the data, shuffling, and loading data in parallel
    # Batch size is set to 32 to fit comfortably in your RTX GPU memory
    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=32, shuffle=True) # Shuffle training data so the model doesn't learn sequence patterns
    val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=32, shuffle=False) # Validation data doesn't need shuffling

    # 4. Set up the device (GPU if available, otherwise CPU)
    # We explicitly check for 'cuda' to utilize your NVIDIA RTX GPU
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # 5. Load the pre-trained ResNet18 model
    # We use weights=models.ResNet18_Weights.DEFAULT to get the best available pre-trained ImageNet weights
    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)

    # 6. Modify the final layer
    # ResNet18 by default outputs 1000 classes (for ImageNet). We only have 2 ('awake' and 'sleepy').
    # model.fc is the final fully connected layer of ResNet18.
    num_ftrs = model.fc.in_features # Get the number of input features to the final layer
    model.fc = nn.Linear(num_ftrs, 2) # Replace the final layer with a new one that outputs 2 features (our 2 classes)

    # Move the entire model to the selected device (CUDA/GPU)
    model = model.to(device)

    # 7. Define the Loss function and Optimizer
    criterion = nn.CrossEntropyLoss() # CrossEntropyLoss is standard for multi-class (or binary) classification tasks
    optimizer = optim.Adam(model.parameters(), lr=0.001) # Adam optimizer with a learning rate of 0.001 to update the model weights

    # 8. Training Loop
    num_epochs = 5
    for epoch in range(num_epochs):
        print(f'Epoch {epoch+1}/{num_epochs}')
        print('-' * 10)

        # --- Training Phase ---
        model.train() # Set the model to training mode (enables dropout, batch normalization updates, etc.)
        running_loss = 0.0 # Variable to accumulate the loss over the epoch

        # Iterate over batches of training data
        for inputs, labels in train_loader:
            inputs = inputs.to(device) # Move the input images to the GPU
            labels = labels.to(device) # Move the corresponding labels to the GPU

            optimizer.zero_grad() # Clear the gradients from the previous batch to prevent accumulation

            outputs = model(inputs) # Forward pass: pass the images through the model to get predictions
            loss = criterion(outputs, labels) # Calculate the error (loss) between predictions and actual labels
            
            loss.backward() # Backward pass: compute the gradients of the loss with respect to model parameters
            optimizer.step() # Update the model parameters using the computed gradients and the Adam optimizer

            running_loss += loss.item() * inputs.size(0) # Accumulate the batch loss (multiplied by batch size to get total loss)

        # Calculate average training loss for this epoch
        epoch_loss = running_loss / len(train_dataset)
        print(f'Training Loss: {epoch_loss:.4f}')

        # --- Validation Phase ---
        model.eval() # Set the model to evaluation mode (disables dropout, fixes batch normalization stats, etc.)
        running_corrects = 0 # Variable to accumulate the number of correct predictions

        # We use torch.no_grad() during validation to disable gradient computation, saving memory and speeding up execution
        with torch.no_grad():
            # Iterate over batches of validation data
            for inputs, labels in val_loader:
                inputs = inputs.to(device) # Move validation images to GPU
                labels = labels.to(device) # Move validation labels to GPU

                outputs = model(inputs) # Forward pass: get predictions
                _, preds = torch.max(outputs, 1) # Get the index of the maximum predicted value (the predicted class index)
                
                # Accumulate the number of correct predictions by comparing with true labels
                running_corrects += torch.sum(preds == labels.data)

        # Calculate validation accuracy for this epoch
        epoch_acc = running_corrects.double() / len(val_dataset)
        print(f'Validation Accuracy: {epoch_acc:.4f}\n')

    # 9. Save the trained model
    # We save the model's state dictionary (which contains all the learned weights and biases) to a file
    torch.save(model.state_dict(), 'drowsiness_model.pth')
    print("Model saved to 'drowsiness_model.pth'")

if __name__ == '__main__':
    main()
