# SmartPy compiler Web IDE implemenation - Smart Contract language for Tezos

SmartPy is an intuitive and powerful smart contract development platform for Tezos

## Running the application

```python
 Run with:
        serve -s -l 3333
    OR
        python3 -m http.server 3333
```

## Usage

On clicking generate button. Following function is executed.
(Check console tab in devtools for the output generated)

It takes one argument which is stringified SmartPy code and returns object.

```javascript
window.runCode(`smartpy code goes here`);
```

### Incase code compiles successfully

```javascript
{
  result: [
    {
      code: '',
      initialStorage: '',
    },
  ];
  success: true;
}
```

> Note: For converting plain michelson code into JSON object, [taquito-michel-codec](https://github.com/ecadlabs/taquito/tree/master/packages/taquito-michel-codec) library can be used.

### Incase code doesn't compiles successfully

```javascript
{
  error: '';
  success: false;
}
```

[Helpful link for understanding how SmartPy works under the hood.](https://www.youtube.com/watch?v=z8YN2oT2gGY)
