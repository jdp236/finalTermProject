# -*- coding: utf-8 -*-
"""palacio_juan_finaltermproj.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1YwK0i4EQZqvYgv-UQflW0CI4rztizQMs

### 1. Import Lib & Dataset
"""

# Adding the script in case Prof or TA need it.

#!pip install tensorflow
#from tensorflow.keras.optimizers import Adam # import Adam optimizer

# Core Libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Scikit-Learn
from sklearn.manifold import TSNE
from sklearn.model_selection import train_test_split, StratifiedKFold, KFold, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, confusion_matrix, ConfusionMatrixDisplay, roc_curve, auc, brier_score_loss, roc_auc_score

# TensorFlow / Keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv1D, Dense, Flatten, MaxPooling1D, Input
from tensorflow.keras.utils import to_categorical


cervic = pd.read_csv('cervical_cancer_risk_classification.csv')

"""### 2. Pre-processing"""

cervic = pd.read_csv('cervical_cancer_risk_classification.csv')

cervic.describe()

cervic.info()

cervic.tail(30)

"""Per the previous line of code some "?" were identified and where I ran the **`cervic.info()`** I saw multiple columns as object so despite of being non-null it could still contain bad data, so let's explore further."""

# Check for "?" in each column
question_marks = cervic.isin(["?"]).sum()
print(question_marks[question_marks > 0])

"""My hypothesis was correct, now I have the total count of bad data (rows containing "?") So let's clean this dataset."""

# Let's replace '?' with NaN
cervic = cervic.replace('?', np.nan)
cervic

cervic.info()

"""Now we can clearly identify that 2 columns have plenty of bad data or missing values. Now it's time to clean it."""

cervic = cervic.drop(columns = ['STDs: Time since first diagnosis','STDs: Time since last diagnosis'])
cervic.info()

"""According to the updated `cervic.info()` results it seems we no longer have those columns, now let's convert columns with datatype object to numeric"""

cervic = cervic.apply(pd.to_numeric, errors='coerce')
cervic.info()

cervic.describe()

cervic.head(100)

"""It seems that there are still some NaN values, let's get the final count for all the columns"""

nan_counts = cervic.isna().sum()
print(nan_counts)

"""**Inputing missing data using the average value. Why?**

*   Deleting rows with missing values would result in significant data loss, reducing the already limited amount of information available for training the model.
*   For example, the dataset only has 858 rows, and dropping rows with missing values could drastically affect the representation of the data.
*   The authors of the paper "Supervised deep learning embeddings for the prediction of cervical cancer diagnosis" used mean imputation to handle missing data, stating, "We scaled all the features in our experiments using [0,1] normalization, and we input missing data using the average value" (Fernandes et al.)
> Fernandes, Kelwin, et al. "Supervised deep learning embeddings for the prediction of cervical cancer diagnosis." PeerJ Computer Science, vol. 4, 2018, p. e154. https://doi.org/10.7717/peerj-cs.154.

















"""

# Replace null values with mean
cervic = cervic.fillna(cervic.mean())
cervic

cervic.describe()

"""Let's double check that all the NaN are gone:"""

nan_counts = cervic.isna().sum()
print(nan_counts)

"""### 3. Data Visualization"""

# Define a function to shorten titles
def shorten_title(title, max_len=10):
    return title if len(title) <= max_len else title[:max_len] + "..."

# Set a consistent style for better visuals
plt.style.use("ggplot")

# Create histograms
ax = cervic.hist(bins=10, figsize=(30, 30), color="#86bf91", edgecolor="black", grid=False)

# Enhance each subplot
for row in ax:
    for subplot in row:
        # Shorten long titles
        subplot.set_title(shorten_title(subplot.get_title()), fontsize=14)
        # Add better x and y labels
        subplot.set_xlabel("Value Range", fontsize=12)
        subplot.set_ylabel("Frequency", fontsize=12)

# Adjust layout for clarity
plt.tight_layout()
plt.show()

# Compute the correlation matrix
corr_matrix = cervic.corr()

# Set up the matplotlib figure
plt.figure(figsize=(15, 15))

# Use a diverging colormap for better distinction between positive and negative correlations
sns.heatmap(
    corr_matrix,
    annot=True,  # Annotate cells with correlation coefficients
    fmt=".1f",   # Format to show numbers with 1 decimal place
    cmap="coolwarm",  # Color map for visualization
    cbar=True,   # Show the color bar
    square=True, # Ensure squares for clarity
    linewidths=0.5,  # Add gridlines
    annot_kws={"size": 10}  # Adjust annotation font size
)

# Add titles and labels for clarity
plt.title("Correlation Matrix", fontsize=16)
plt.xticks(rotation=45, ha="right", fontsize=10)
plt.yticks(rotation=0, fontsize=10)

# Show the plot
plt.tight_layout()
plt.show()

"""*   This correlation matrix allow us to understand if there is high, low or no corerlation between features

*   There are some highly correlated cases like **Smokes** and **Smokes (years)** (Correlation: **0.7**)

*   Also there is a high correlation between **STD numbers** and **STDs:condylomatosis** (**0.9**)
*   I'm deciding not to drop  any features now to ensure the models could learn patterns from the complete dataset, but I might have the time to implement deep supervised encoders to fight dimensionality and correlation.

**Understanding the target variable.**

The final four columns (“Hinselmann,” “Schiller,” “Citology,” and “Biopsy”) represent the outcomes of various cervical cancer screening tests. A positive result in any of these tests does not necessarily confirm a diagnosis of cervical cancer. However, the likelihood of cervical cancer increases as more tests return positive results.
To capture this cumulative risk, I introduced a new variable, CervicalCancer, calculated as the sum of the four test results:


> **CervicalCancer**=Hinselmann+Schiller+Citology+Biopsy
"""

# Create the 'CervicalCancer' column by summing the relevant columns
cervic['CervicalCancer'] = cervic[['Hinselmann', 'Schiller', 'Citology', 'Biopsy']].sum(axis=1)

# Calculate the proportion of each value in 'CervicalCancer'
cervical_cancer_dist = cervic['CervicalCancer'].value_counts(normalize=True).sort_index()
print(cervical_cancer_dist.round(2))
colors = {
    0: 'skyblue',
    1: 'orange',
    2: 'green',
    3: 'red',
    4: 'purple'
}
plt.figure(figsize=(8, 6))
bars = plt.bar(
    cervical_cancer_dist.index,
    cervical_cancer_dist.values,
    color=[colors[int(score)] for score in cervical_cancer_dist.index],
    edgecolor='black'
)
plt.title('Distribution of CervicalCancer Target Variable', fontsize=14)
plt.xlabel('CervicalCancer Score (Summation)', fontsize=12)
plt.ylabel('Proportion', fontsize=12)
plt.xticks(ticks=cervical_cancer_dist.index, labels=cervical_cancer_dist.index.astype(int), rotation=0)
plt.grid(axis='y', linestyle='--', alpha=0.7)
legend_labels = [
    plt.Line2D([0], [0], color=color, lw=4, label=f'{score} = {"None" if score == 0 else ["Hinselmann", "Schiller", "Citology", "Biopsy"][score - 1]}')
    for score, color in colors.items()
]
plt.legend(handles=legend_labels, loc='upper right', title='CervicalCancer Scores', fontsize=10)
plt.show()

"""### 4.Pre-Modeling

#### **4.1 Split the dataset into features (X) and target label (y)**
"""

# Define features and target
X = cervic.drop(columns=['Biopsy'])  # Exclude target column
y = cervic['Biopsy']  # Target variable

# Perform train-test split with 10% test size and stratification
features_train_all, features_test_all, labels_train_all, labels_test_all = train_test_split(
    X, y, test_size=0.1, random_state=21, stratify=y
)

# Reset indices for the training and testing sets
for dataset in [features_train_all, features_test_all, labels_train_all, labels_test_all]:
    dataset.reset_index(drop=True, inplace=True)

# Check shapes of the resulting datasets
print("Training Features Shape:", features_train_all.shape)
print("Testing Features Shape:", features_test_all.shape)
print("Training Labels Shape:", labels_train_all.shape)
print("Testing Labels Shape:", labels_test_all.shape)

"""#### **4.2 Normalize data**"""

# Initialize the scaler
scaler = StandardScaler()

# Fit the scaler on the training data and transform both train and test datasets
features_train_all_std = scaler.fit_transform(features_train_all)
features_test_all_std = scaler.transform(features_test_all)

# Perform train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Convert back to DataFrame for compatibility if needed
features_train_all_std = pd.DataFrame(features_train_all_std, columns=features_train_all.columns)
features_test_all_std = pd.DataFrame(features_test_all_std, columns=features_test_all.columns)

features_train_all_std

"""### Selecting Classification Models

*   Random Forest
*   KNN
*   Conv1D

#### **4.2 Randon Forest Parameter Tuning**
"""

# Define the parameter grid for Random Forest
param_grid_rf = {
    'n_estimators': [50, 100, 200],
    'max_depth': [None, 10, 20, 30],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4]
}

# Initialize Random Forest Classifier
rf_classifier = RandomForestClassifier(random_state=42)

# Perform GridSearchCV
grid_search_rf = GridSearchCV(estimator=rf_classifier, param_grid=param_grid_rf, cv=5, scoring='accuracy', verbose=1)
grid_search_rf.fit(X_train, y_train)

print("Best Parameters for Random Forest:", grid_search_rf.best_params_)
print("Best Score for Random Forest:", grid_search_rf.best_score_)

"""#### **4.3 KNN Parameter Tuning**"""

# Define the parameter grid for KNN
param_grid_knn = {
    'n_neighbors': [3, 5, 7, 9],
    'weights': ['uniform', 'distance'],
    'metric': ['euclidean', 'manhattan', 'minkowski']
}

# Initialize KNN Classifier
knn_classifier = KNeighborsClassifier()

# Perform GridSearchCV
grid_search_knn = GridSearchCV(estimator=knn_classifier, param_grid=param_grid_knn, cv=5, scoring='accuracy', verbose=1)
grid_search_knn.fit(X_train, y_train)

print("Best Parameters for KNN:", grid_search_knn.best_params_)
print("Best Score for KNN:", grid_search_knn.best_score_)

"""#### **4.4 Conv1D Parameter Tuning**"""

# Normalize and reshape the data
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

X_train_reshaped = X_train_scaled.reshape(X_train_scaled.shape[0], X_train_scaled.shape[1], 1)
X_test_reshaped = X_test_scaled.reshape(X_test_scaled.shape[0], X_test_scaled.shape[1], 1)

# Function to create Conv1D model
def create_conv1d_model(filters, kernel_size, pool_size, dense_units, input_shape):
    model = Sequential([
        Conv1D(filters=filters, kernel_size=kernel_size, activation='relu', input_shape=input_shape),
        MaxPooling1D(pool_size=pool_size),
        Flatten(),
        Dense(dense_units, activation='relu'),
        Dense(1, activation='sigmoid')  # Binary classification
    ])
    model.compile(optimizer=Adam(), loss='binary_crossentropy', metrics=['accuracy'])
    return model

# Parameter tuning (manual grid search)
filter_sizes = [32, 64]
kernel_sizes = [3, 5]
pool_sizes = [2, 3]
dense_units = [50, 100]

best_model = None
best_accuracy = 0

for filters in filter_sizes:
    for kernel_size in kernel_sizes:
        for pool_size in pool_sizes:
            for dense_unit in dense_units:
                model = create_conv1d_model(filters, kernel_size, pool_size, dense_unit, input_shape=(X_train_reshaped.shape[1], 1))
                model.fit(X_train_reshaped, y_train, epochs=5, batch_size=32, verbose=0)
                loss, accuracy = model.evaluate(X_test_reshaped, y_test, verbose=0)
                print(f"Filters: {filters}, Kernel Size: {kernel_size}, Pool Size: {pool_size}, Dense Units: {dense_unit}, Accuracy: {accuracy:.4f}")
                if accuracy > best_accuracy:
                    best_model = model
                    best_accuracy = accuracy

print(f"Best Conv1D Model Accuracy: {best_accuracy:.4f}")

"""### 10-Fold Cross Validation"""

from sklearn.model_selection import StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix, brier_score_loss, roc_auc_score
from keras.models import Sequential
from keras.layers import Conv1D, MaxPooling1D, Flatten, Dense, Input
import pandas as pd
import numpy as np

# Define the metrics calculation function
def calc_metrics(conf_matrix):
    TP, FN = conf_matrix[0][0], conf_matrix[0][1]
    FP, TN = conf_matrix[1][0], conf_matrix[1][1]
    TPR = TP / (TP + FN) if (TP + FN) > 0 else 0
    TNR = TN / (TN + FP) if (TN + FP) > 0 else 0
    FPR = FP / (TN + FP) if (TN + FP) > 0 else 0
    FNR = FN / (TP + FN) if (TP + FN) > 0 else 0
    Precision = TP / (TP + FP) if (TP + FP) > 0 else 0
    F1_measure = 2 * TP / (2 * TP + FP + FN) if (2 * TP + FP + FN) > 0 else 0
    Accuracy = (TP + TN) / (TP + FP + FN + TN)
    Error_rate = (FP + FN) / (TP + FP + FN + TN)
    BACC = (TPR + TNR) / 2
    TSS = TPR - FPR
    HSS = 2 * (TP * TN - FP * FN) / ((TP + FN) * (FN + TN) + (TP + FP) * (FP + TN)) if ((TP + FN) * (FN + TN) + (TP + FP) * (FP + TN)) > 0 else 0
    return [TP, TN, FP, FN, TPR, TNR, FPR, FNR, Precision, F1_measure, Accuracy, Error_rate, BACC, TSS, HSS]

# Define the function to calculate metrics for a given model
def get_metrics(model, X_train, X_test, y_train, y_test, Conv1D_flag=False):
    metrics = []

    if Conv1D_flag:
        # Prepare Conv1D data
        X_train, X_test = map(np.array, [X_train, X_test])
        X_train_reshaped = X_train.reshape(len(X_train), X_train.shape[1], 1)
        X_test_reshaped = X_test.reshape(len(X_test), X_test.shape[1], 1)

        # Train Conv1D model
        model.fit(X_train_reshaped, y_train, epochs=5, batch_size=32, verbose=0)

        # Predictions and metrics
        predict_prob = model.predict(X_test_reshaped).flatten()
        pred_labels = (predict_prob > 0.5).astype(int)
        conf_matrix = confusion_matrix(y_test, pred_labels, labels=[1, 0])
        brier_score = brier_score_loss(y_test, predict_prob)
        roc_auc = roc_auc_score(y_test, predict_prob)

        metrics.extend(calc_metrics(conf_matrix))
        metrics.extend([brier_score, roc_auc])

    else:
        # Train traditional model
        model.fit(X_train, y_train)
        predict_prob = model.predict_proba(X_test)[:, 1]
        predicted = model.predict(X_test)
        conf_matrix = confusion_matrix(y_test, predicted, labels=[1, 0])
        brier_score = brier_score_loss(y_test, predict_prob)
        roc_auc = roc_auc_score(y_test, predict_prob)

        metrics.extend(calc_metrics(conf_matrix))
        metrics.extend([brier_score, roc_auc])

    return metrics

# Initialize variables
cv_stratified = StratifiedKFold(n_splits=10, shuffle=True, random_state=21)
metric_columns = ['TP', 'TN', 'FP', 'FN', 'TPR', 'TNR', 'FPR', 'FNR', 'Precision',
                  'F1_measure', 'Accuracy', 'Error_rate', 'BACC', 'TSS', 'HSS',
                  'Brier_score', 'AUC']
knn_metrics_list, rf_metrics_list, conv1d_metrics_list = [], [], []

# Define the best hyperparameters
best_n_neighbors = 5
best_rf_params = {'n_estimators': 100, 'min_samples_split': 2, 'min_samples_leaf': 1}

# Perform cross-validation
for iter_num, (train_index, test_index) in enumerate(cv_stratified.split(features_train_all_std, labels_train_all), start=1):
    features_train, features_test = features_train_all_std.iloc[train_index, :], features_train_all_std.iloc[test_index, :]
    labels_train, labels_test = labels_train_all.iloc[train_index], labels_train_all.iloc[test_index]

    # KNN
    knn_model = KNeighborsClassifier(n_neighbors=best_n_neighbors)
    knn_metrics = get_metrics(knn_model, features_train, features_test, labels_train, labels_test, Conv1D_flag=False)
    knn_metrics_list.append(knn_metrics)

    # Random Forest
    rf_model = RandomForestClassifier(**best_rf_params, random_state=21)
    rf_metrics = get_metrics(rf_model, features_train, features_test, labels_train, labels_test, Conv1D_flag=False)
    rf_metrics_list.append(rf_metrics)

    # Conv1D
    conv1d_model = Sequential([
        Input(shape=(features_train.shape[1], 1)),
        Conv1D(filters=32, kernel_size=3, activation='relu'),
        MaxPooling1D(pool_size=2),
        Flatten(),
        Dense(100, activation='relu'),
        Dense(1, activation='sigmoid')
    ])
    conv1d_model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    conv1d_metrics = get_metrics(conv1d_model, features_train, features_test, labels_train, labels_test, Conv1D_flag=True)
    conv1d_metrics_list.append(conv1d_metrics)

    # Display iteration results
    metrics_all_df = pd.DataFrame([knn_metrics, rf_metrics, conv1d_metrics], columns=metric_columns, index=['KNN', 'RF', 'Conv1D'])
    print(f"\nIteration {iter_num}:\n")
    print(metrics_all_df.round(2).T)

# Aggregate final results
final_metrics_df = pd.DataFrame([
    pd.DataFrame(knn_metrics_list, columns=metric_columns).mean(),
    pd.DataFrame(rf_metrics_list, columns=metric_columns).mean(),
    pd.DataFrame(conv1d_metrics_list, columns=metric_columns).mean()
], index=['KNN', 'RF', 'Conv1D'])

print("\nFinal Average Metrics Across Folds:\n")
print(final_metrics_df.round(2).T)

"""#### Metrics"""

# Initialize metric index for each iteration
metric_index_df = ['iter1', 'iter2', 'iter3', 'iter4', 'iter5', 'iter6', 'iter7', 'iter8', 'iter9', 'iter10']

# Create DataFrames for each algorithm's metrics
knn_metrics_df = pd.DataFrame(knn_metrics_list, columns=metric_columns, index=metric_index_df)
rf_metrics_df = pd.DataFrame(rf_metrics_list, columns=metric_columns, index=metric_index_df)
conv1d_metrics_df = pd.DataFrame(conv1d_metrics_list, columns=metric_columns, index=metric_index_df)

# Display metrics for each algorithm in each iteration
for i, (algorithm_name, metrics_df) in enumerate(
        zip(['KNN', 'Random Forest', 'Conv1D'],
            [knn_metrics_df, rf_metrics_df, conv1d_metrics_df]), start=1):
    print(f'\nMetrics for Algorithm {algorithm_name}:\n')
    print(metrics_df.round(decimals=2).T)
    print('\n')

# Aggregate metrics across iterations for final analysis
knn_avg_metrics = knn_metrics_df.mean()
rf_avg_metrics = rf_metrics_df.mean()
conv1d_avg_metrics = conv1d_metrics_df.mean()

# Combine final average metrics into a summary DataFrame
final_metrics_summary_df = pd.DataFrame(
    [knn_avg_metrics, rf_avg_metrics, conv1d_avg_metrics],
    columns=metric_columns,
    index=['KNN', 'Random Forest', 'Conv1D']
)

print("\nFinal Average Metrics Across 10 Iterations:\n")
print(final_metrics_summary_df.round(decimals=2).T)

"""#### Average metric for each algorithm"""

# Calculate the average metrics for each algorithm
knn_avg_df = knn_metrics_df.mean()
rf_avg_df = rf_metrics_df.mean()
conv1d_avg_df = conv1d_metrics_df.mean()

# Create a DataFrame with the average performance for each algorithm
avg_performance_df = pd.DataFrame(
    {'KNN': knn_avg_df, 'RF': rf_avg_df, 'Conv1D': conv1d_avg_df},
    index=metric_columns
)

# Display the average performance for each algorithm
print("Average Performance Metrics for Each Algorithm:\n")
print(avg_performance_df.round(decimals=2))

"""#### Evaluating the performance of various algorithms by comparing their ROC curves and AUC scores on the test dataset."""

#KNN

# Function to plot ROC curves for a given model
def plot_roc_curve(model, X_test, y_test, model_name, is_conv1d=False):
    """
    Plot the ROC curve for a given model.

    Args:
    - model: The trained model.
    - X_test: Test features.
    - y_test: Test labels.
    - model_name: Name of the model (e.g., 'KNN', 'RF', 'Conv1D').
    - is_conv1d: Boolean indicating if the model is Conv1D-based.
    """
    if is_conv1d:
        # Reshape test data for Conv1D
        X_test = X_test.values.reshape(X_test.shape[0], X_test.shape[1], 1)
        y_score = model.predict(X_test).ravel()  # Flatten probabilities
    else:
        # Get predicted probabilities
        y_score = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else model.predict(X_test)

    # Compute ROC curve and AUC
    fpr, tpr, _ = roc_curve(y_test, y_score)
    roc_auc = auc(fpr, tpr)

    # Plot the ROC curve
    plt.figure(figsize=(8, 8))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label='ROC curve (area = {:.2f})'.format(roc_auc))
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title(f'{model_name} ROC Curve')
    plt.legend(loc='lower right')
    plt.show()

# Evaluate KNN
knn_model = KNeighborsClassifier(n_neighbors=best_n_neighbors)
knn_model.fit(features_train_all_std, labels_train_all)
plot_roc_curve(knn_model, features_test_all_std, labels_test_all, model_name="KNN")

# Evaluate Random Forest
rf_model = RandomForestClassifier(**best_rf_params, random_state=21)
rf_model.fit(features_train_all_std, labels_train_all)
plot_roc_curve(rf_model, features_test_all_std, labels_test_all, model_name="Random Forest")

# Evaluate Conv1D
conv1d_model = Sequential([
    Input(shape=(features_train_all_std.shape[1], 1)),
    Conv1D(filters=32, kernel_size=3, activation='relu'),
    MaxPooling1D(pool_size=2),
    Flatten(),
    Dense(100, activation='relu'),
    Dense(1, activation='sigmoid')  # Binary classification
])
conv1d_model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
# Reshape training data for Conv1D
features_train_reshaped = features_train_all_std.values.reshape(features_train_all_std.shape[0], features_train_all_std.shape[1], 1)
conv1d_model.fit(features_train_reshaped, labels_train_all, epochs=5, batch_size=32, verbose=0)
plot_roc_curve(conv1d_model, features_test_all_std, labels_test_all, model_name="Conv1D", is_conv1d=True)