import theano
import theano.tensor as T
import pandas as pd
import numpy as np
import random
import matplotlib.pyplot as plt

from .initilizations import init_params
from .activations import tanh, sigmoid, relu, softplus
from .losses import mean_squared_error, binary_cross_entropy

"""
DeepLearning website - Yoshua Bengio:
- http://deeplearning.net/tutorial/mlp.html
"""

## TODO: add batch
## TODO: comment out

T_activations = {None: None,
                'linear': None,
                'tanh': T.tanh,
                'sigmoid': T.nnet.sigmoid,
                'relu': T.nnet.relu,
                'softplus': T.nnet.softplus,
                }

activations = {None: None,
                'linear': None,
                'tanh': tanh,
                'sigmoid': sigmoid,
                'relu': relu,
                'softplus': softplus,
                }
        
class Layer(object):
    def __init__(self, n_in, n_out, W=None, b=None, activation=None, seed=None, init_weights='xavier', init_bias='zeros'):
      
        self.input = input
        self.activation = activation
        self.f = T_activations[activation]
        self.activate = activations[activation]

        if W is None:
            # If weights matrix is not provided (default), initialize from a distribution
            W_values = init_params(rows=n_in, cols=n_out, method=init_weights, seed=seed)
            # Multiply by 4 the weights for sigmoid activation. See Y. Bengio's website
            if activation == theano.tensor.nnet.sigmoid:
                W_values *= 4
        elif W.shape == (n_in, n_out):
            raise ValueError(f'Weights dimension does not match. Dimension for W should be {(n_in, n_out)} and got {W.shape}.')

        if b is None:
            # If bias matrix is not provided (default), initialize from a distribution
            b_values = init_params(rows=1, cols=n_out, method=init_bias, seed=seed)
        elif b.shape == (n_in, n_out):
            raise ValueError(f'Weights dimension does not match. Dimension for b should be {(1, n_out)} and got {b.shape}.')
        
        # Share parameters with theano
        W = theano.shared(value=W_values, name='W', borrow=True)
        b = theano.shared(value=b_values, name='b', borrow=True)

        # Store parameters in the class
        self.W = W
        self.b = b
        
        # Parameters of the model
        self.params = [self.W, self.b]

    def feed_forward(self, input, tensor=True):
        if tensor:
            Xb_e = T.dot(input, self.W) + self.b
            self.output = (Xb_e if self.activation in [None, 'linear'] else self.f(Xb_e))
        else:
            # Used as feed forward for prediction (avoid using Theano)
            Xb_e = input.dot(self.W.get_value()) + self.b.get_value()
            self.output = (Xb_e if self.activation in [None, 'linear'] else self.activate(Xb_e))
        return self.output

class MLP:
    def __init__(self, loss='MSE', optimizer='sgd', random=None):
        self.loss = loss
        self.optimizer = optimizer
        self._layers = []
        self.params = []
        self.L1 = 0.
        self.L2 = 0.
        self._cost = []

    def _L1(self):
        
        for layer in self._layers:
            # L1 norm ; one regularization option is to enforce L1 norm to
            # be small
            self.L1 += abs(layer.W).sum()
        return self.L1
    
    def _L2(self):
        for layer in self._layers:
            # square of L2 norm ; one regularization option is to enforce
            # square of L2 norm to be small
            self.L2 += (layer.W ** 2).sum()
        return self.L2
    
    def _params(self):
        # the parameters of the model are the parameters of the two layer it is
        # made out of
        _params = []
        for layer in self._layers:
            _params += list(layer.params)
        
        self.params = list(_params)
    
    def add(self, layer):
        
        self._layers.append(layer)
    
    def forward_prop(self, x, tensor=True):
        output = x
        for layer in self._layers:
            output = layer.feed_forward(output, tensor)
        return output

    def cost(self, x, y):
        output = self.forward_prop(x)
        # Compute loss
        if self.loss.lower() in ['mse', 'mean_squared_error']:
            _cost = mean_squared_error(y_true=y, y_pred=output) # ((output - y) ** 2).sum()
        elif self.loss.lower() in ['binary_cross_entropy', 'bce']:
            _cost = binary_cross_entropy(y_true=y, y_pred=output)
        else:
            raise ValueError('Loss function is not valid.')
        self._cost += [_cost]
        return _cost
    
    def get_weights(self, layer='all', param='all'):
        """
        Fetches the parameters from the network.
        
        Parameters
        ----------
        layer: int
            Layer id from which to fetch the parameters (defaults 'all').
        param: str
            What parameter we need to fetch (defaults 'all').
        
        Returns
        -------
        weights: dict
            The parameters in the network.
        """
        # Check what parameter the user was to get
        if param.lower() in ['weights', 'w', 'weight']:
            par = 0
        elif param.lower() in ['biases', 'b', 'bias']:
            par = 1
        elif param.lower() == 'all':
            par = 2
        else:
            raise ValueError('Value for "param" is not value. Please chose between "weights", "bias" or "all".')
        
        if layer == 'all':
            # If user wants to see all layers, we create a dictionnary
            weights = {}
            for i in range(len(self._layers)):
                if par == 0:
                    weights.update({f'weights {i}': self._layers[i].params[0].get_value()})
                elif par == 1:
                    weights.update({f'bias {i}': self._layers[i].params[1].get_value()})
                else:
                    weights.update({f'weights {i}': self._layers[i].params[0].get_value(), f'bias {i}': self._layers[i].params[1].get_value()})
        elif layer in range(len(self._layers)):
            # If user wants only 1 specific layer,
            if par == 2:
                # we return a dict for all params
                weights = {'weights': self._layers[layer].params[0].get_value(), 'bias': self._layers[layer].params[1].get_value()}
            else:
                # or an array for 1 single param
                weights = self._layers[layer].params[0].get_value()
        else:
            raise ValueError(f'Layer is incorrect. Please chose either "all" or layer <= {len(self._layers) - 1}. Got layer = {layer}')
        
        return weights
 
    def train(self, data, X, Y='Y', epochs=100, batch_size=1, training_size=0.8, test_set=None, learning_rate=0.01, L1_reg=0., L2_reg=0., early_stop=True, patience=100, improvement_threshold=0.995, restore_weights=True, verbose=False, plot=False):
        """
        Train the Neural Network.
        
        Parameters
        ----------
        data: pd.DataFrame
            Layer id from which to fetch the parameters.
        X: list
            List of X input variables.
        Y: str
            Variable to predict (defaults 'Y').
        epochs: int
            Number of epochs to train (defaults 100).
        batch_size: int
            Size of each batch to be trained (defaults 1).
        learning_rate: float
            Learning rate for gradient descent (defaults 0.01).
        patience: int
            Look as this many examples regardless (defaults 100).
        improvement_threshold: float
            Relative improvement to be considered as significant (defaults 0.995).
        L1_reg: float
            L1 regularization rate (defaults 0.0)
        L2_reg: float
            L2 regularization rate (defaults 0.0)
        
        Returns
        -------
        weights: dict
            The parameters in the network.
        """
        # Parse arguments to pass to self
        self.learning_rate = learning_rate
        self.L1_reg = L1_reg
        self.L2_reg = L2_reg
        self.X_col = X
        self.Y_col = Y

        # Get indexes
        self.data_size = data.shape[0]

        if test_set is None:
            data_idx = list(data.index)
            train_index = random.sample(data_idx, int(self.data_size * training_size))
            test_index = [i for i in data_idx if i not in train_index]
            # Train set
            valid_set_x = data.loc[train_index, self.X_col]
            valid_set_y = data.loc[train_index, self.Y_col]
            # Test set
            test_set_x = data.loc[test_index, self.X_col]
            test_set_y = data.loc[test_index, self.Y_col]
        else:
            # Train set
            valid_set_x = data[self.X_col]
            valid_set_y = data[self.Y_col]
            # Test set
            test_set_x = test_set[self.X_col]
            test_set_y = test_set[self.Y_col]
        
        # Set data to theano
        # Train set
        valid_set_x = theano.shared(np.array(valid_set_x, dtype=theano.config.floatX))
        valid_set_y = theano.shared(np.array(valid_set_y, dtype=theano.config.floatX))
        # Test set
        test_set_x = theano.shared(np.array(test_set_x, dtype=theano.config.floatX))
        test_set_y = theano.shared(np.array(test_set_y, dtype=theano.config.floatX))
        self.test_set = test_set_x

        index = T.lscalar()  # index to a [mini]batch
        x = T.vector('x')
        y = T.scalar('y')

        # Get initial parameters
        self._params()

        # Set cost
        cost = self.cost(x, y) + (self.L1_reg * self._L1()) + (self.L2_reg * self._L2())
        

        gparams = [T.grad(cost, param) for param in self.params]

        if self.optimizer.lower() in ['sgd', 'stochastic_gradient_descent']:
            updates = [(param, param - self.learning_rate * gparam) for param, gparam in zip(self.params, gparams)]
        else:
            raise ValueError('Optimizer not valid. Please use "sdg"')
        
        # Initialize variables for training
        current_epoch = 0
        done_looping = False
        best_validation_loss = np.inf
        best_iter = 0
        
        train_model = theano.function(
            inputs=[index],
            outputs=cost,
            updates=updates,
            givens={x: valid_set_x[index], y: valid_set_y[index]}
        )

        # theano.function(inputs=[x,y], outputs=[prediction, xent], updates=[[w, w-0.01*gw], [b, b-0.01*gb]], name = "train")
        
        validate_model = theano.function(
            inputs=[index],
            outputs=cost,
            givens={x: test_set_x[index], y: test_set_y[index]}
        )

        # early-stopping parameters
        patience = 10000  # look as this many examples regardless
        # patience_increase = 2  # wait this much longer when a new best is found
        improvement_threshold = 0.995  # a relative improvement of this much is considered significant
        # validation_frequency = 10
        
        n_valid_set = valid_set_x.get_value(borrow=True).shape[0]
        n_test_set = test_set_x.get_value(borrow=True).shape[0] 

        # while (current_epoch < epochs+1) & (not done_looping):
        #     current_epoch += 1
        #     minibatch_avg_cost = [train_model(i) for i in range(n_valid_set)]
        #     minibatch_avg_cost = np.mean(minibatch_avg_cost)
        #     if current_epoch % validation_frequency == 0:
        #         validation_losses = [validate_model(i).tolist() for i in range(n_test_set)]
        #         validation_losses = np.mean(validation_losses)
        #         if validation_losses < best_validation_loss:
        #             if (validation_losses < best_validation_loss * improvement_threshold):
        #                 patience = max(patience, current_epoch * patience_increase)
        #             best_validation_loss = validation_losses
        #             best_iter = current_epoch
        #             print('Epoch %i, validation error %f' %(current_epoch, best_validation_loss))
            
        #     # Check early stopping
        #     if patience <= current_epoch:
        #         done_looping = True
        #         break
        
        # Initialize values
        self.train_losses = []       # Training loss vector to plot
        self.test_losses = []        # Test loss vector to plot
        self.best_loss = np.inf # Initial best loss value
        verif_i = epochs        # First, verify epoch at then end (init only)
        i = 0

        # Start training
        while i <= epochs:
            i += 1
            # Train
            output = [train_model(i) for i in range(n_valid_set)]
            # Evaluate on test set
            test_out = [validate_model(i).tolist() for i in range(n_test_set)]
            # Measure accuracy on train and test sets
            epoch_loss = np.mean([train_model(i) for i in range(n_valid_set)])
            epoch_loss_test = np.mean([validate_model(i).tolist() for i in range(n_test_set)])
            # Save to historical performance
            self.train_losses += [epoch_loss]
            self.test_losses += [epoch_loss_test]
            # If we got the best score until now, and patience is not reached
            if (epoch_loss_test < self.best_loss * improvement_threshold) & (i <= verif_i) & early_stop:
                # pc.verbose_display(f'New min found for iter {i}', verbose=verbose_all)
                verif_i = i + patience
                self.best_loss = epoch_loss_test
                self.best_iter = i
                # self.optimal_w = self.w.get_value()
                # self.optimal_b = self.b.get_value()
            # if no improvement
            elif (i <= verif_i):
                # pc.verbose_display(f'No improvement at iter {i}', verbose=verbose_all)
                pass
            else:
                # pc.verbose_display(f'Stop training. Minimum found after {self.best_iter} iterations', verbose)
                break
        

        if plot:
            # Plot the training and test loss
            plt.title('MLP train vs. test error through epochs', loc='center')
            plt.plot(self.train_losses, label='Training loss')
            plt.plot(self.test_losses, label='Test loss')
            plt.legend()
            plt.show()
    

    def predict(self, new_data, binary=False):
        """
        """
        # Transform input data to be transformed into numpy array format
        x = new_data[self.X_col].values
        # Apply feedforward step to the data to get the prediction (apply weights and activations)
        output = self.forward_prop(x, tensor=False)
        if binary:
            return [1. if y[0] > 0.5 else 0. for y in output.reshape((new_data.shape[0], 1))]
        else:
            return [y[0] for y in output.reshape((new_data.shape[0], 1))]
