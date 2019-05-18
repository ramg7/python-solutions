# least_squares.py
# Python Coding
#
# Created by Roberto Merlos on 3/30/18.
# Copyright © 2019 RAMG. All rights reserved.
#
# Matrices - Least Squares Approximation

import numpy as np
#import math

def test():
    message = "MATRIX SIMPLE TUTORIAL."
    print("—"*len(message))
    print(message)
    print("—"*len(message), "\n\n")
    print("*Matrix 1:")
    x = np.array([1,2])
    print(x)
    print("Shape:", x.shape)
    print("Size:", x.size)
    print("—"*len(message))
    print("*Matrix 2:")
    x = np.array([[1,2],[3,2],[4,2]])
    print(x)
    print("Shape:", x.shape)
    print("Size:", x.size)
    print("\nMatrix 2 Transpose:")
    xt = x.T
    print(xt)
    print("\n(Matrix 2) x (Matrix 2 Transpose):")
    a = xt.dot(x)
    print(a)
    print("\nInverse of result:")
    i = np.linalg.inv(a)
    print(i)
    print("\nInverse of the inverse:")
    i2 = np.linalg.inv(i)
    print(i2)
    print("—"*len(message))
    
    message = "Example of application: Least Squares Approximation"
    print("\n\n")
    print("—"*len(message))
    print(message, "\nfor points: (2,5) & (3,6) [Polynomial of degree 2]")
    print("—"*len(message))
    print("Matrix A:")
    A = np.array([[1, 2, 2**2],[1,3,3**2]])
    print(A)
    print("\nY:")
    Y = np.array([[5,6]]).T
    print(Y)
    print("\nX = (Aᵀ⋅A)⁻¹⋅Aᵀ⋅Y:")
    #r = m.sin(m.pi)

    '''
    A = np.array([[1, 1, 1],[1,10, 100]])
    Y = np.array([[0,40]]).T
    print(A)
    print(Y)
    print(A.T.dot(A))
    print(A.T.dot(Y))
    '''
    
    X = np.linalg.inv(A.T.dot(A)).dot(A.T.dot(Y))
    print(X)
    print("—"*len(message))
                                      
if __name__ == "__main__":
    test()
