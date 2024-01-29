class KeyPressListener {
    constructor(keyCode, callback) {
      this.keydownFunction = function (event) {
        console.log(event.code);
        if (event.code === keyCode) {
          callback();
        }
      };
      document.addEventListener("keydown", this.keydownFunction);
    }
  
    unbind() {
      document.removeEventListener("keydown", this.keydownFunction);
    }
  }