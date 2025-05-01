package workdone;
final class LinearSearch {
    public static void main(String[] args) {

        int arr[] = {-2,40, -14, 0, 39,-1, 30, 55};
        int target = -1;

        int out = linearSearch(arr, target);
        System.out.println(out);

    }

    static int linearSearch(int[] arr, int target){
        if(arr.length == 0){
            return -1;
        }
        for(int index = 0; index< arr.length; index++){
            int element = arr[index];
            if(element == target){
                return index;
            }

        }
        return -1;
    }
    
    
}
