package workdone;
final class BinarySearchTree {
    public static void main(String[] args) throws Exception {
        int arr[] = {-13, -10, -5, 0, 2, 7, 14, 21, 54};
        int target = 2;
        int ans = binarySearch(arr, target);
        System.out.println(ans);
    }

    static int binarySearch(int[] arr, int target){
        int start = 0;
        int end = arr.length- 1;

        while(start<= end){

            int mid = start +(end - start)/2;
            
            if(target< arr[mid]){
                end = mid -1;
            }else if(target> arr[mid]){
                end = mid +1;
            }else{
                return mid;
            }
        }

        return -1;
    }
}
