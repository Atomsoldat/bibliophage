[Every vue application is instantiated](https://vuejs.org/guide/essentials/application.html) through the `createApp()` function. In our case, we instantiate `App`, which is defined in `App.vue`. That file then pulls in all the other Vue stuff we use.

```
main.ts
  └──createApp(App)
       └── App.vue
            ├── Sidebar.vue
            └── router-view (loads other pages)
```
