// This file teaches Typescript which Type to assign to imported files ending in .vue
// https://www.typescriptlang.org/docs/handbook/2/type-declarations.html 
declare module '*.vue' {
  import { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}
