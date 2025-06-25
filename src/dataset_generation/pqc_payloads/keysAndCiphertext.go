package main

import (
  //"fmt"
  kyberk2so "github.com/symbolicsoft/kyber-k2so"
  "os"
)

func main() {
  // Generate key-pair
  dk, ek, _ := kyberk2so.KemKeypair512()

  // Get ciphertext and shared secret from public key
  c, _, _ := kyberk2so.KemEncrypt512(ek)

  os.Stdout.Write(dk[:])
  os.Stdout.Write(c[:])
}
