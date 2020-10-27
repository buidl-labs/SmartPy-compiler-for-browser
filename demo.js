const sample = `# Store Value - Example for illustrative purposes only.

import smartpy as sp

class StoreValue(sp.Contract):
    def __init__(self, value):
        self.init(storedValue = value)

    @sp.entry_point
    def replace(self, params):
        self.data.storedValue = params.value

    @sp.entry_point
    def double(self, params):
        self.data.storedValue *= 2

    @sp.entry_point
    def divide(self, params):
        sp.verify(params.divisor > 5)
        self.data.storedValue /= params.divisor

if "templates" not in __name__:
    @sp.add_test(name = "StoreValue")
    def test():
        c1 = StoreValue(12)
        scenario = sp.test_scenario()
        scenario.h1("Store Value")
        scenario += c1
        scenario += c1.replace(value = 15)
        scenario.p("Some computation").show(c1.data.storedValue * 12)
        scenario += c1.replace(value = 25)
        scenario += c1.double()
        scenario += c1.divide(divisor = 2).run(valid = False)
        scenario.verify(c1.data.storedValue == 50)
        scenario += c1.divide(divisor = 6)
        scenario.verify(c1.data.storedValue == 8)
`;

let id = 0;
window.nextId = () => ++id;

window.editor = {
  getValue: () => codeEl.value,
  appendOutput: (output) => (outputEl.value += output),
};

window.runCode = (code) => {
  try {
    const results = generate(code);

    console.log(JSON.parse(results));
  } catch (error) {
    const er = showTraceback(error, '' + error);
    console.log(JSON.parse(er));
  }
};
